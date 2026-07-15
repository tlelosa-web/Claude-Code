"""Regression test for the WO Edit page "Add as component of…" nesting fix.

Root cause (see docs/specs/dashboard-bom-ui-fixes-2026-07-15.md, item 3):
addItemFromCatalogue() in templates/works_orders/edit.html always built a
flat-row appended to the end of the table, with no way to nest a newly
added item as a component-row under an existing assembly-row. Removing a
component and re-adding its replacement therefore always produced a new
top-level ASSEMBLY_ITEM/flat line instead of a nested COMPONENT.

There is no JS test runner in this repo (no package.json/Jest/Playwright),
so this test exercises the same route the corrected JS now posts to
(POST /works-orders/<id>/edit with bom_items_json) with the payload shape
the fixed addItemFromCatalogue()/syncEditJSON() produce when "Add as
component of [assembly]" is selected: a COMPONENT nested inside the
assembly's `components` array, not a new top-level entry. This asserts the
saved BOM ends up correctly nested — the persisted, observable behaviour
that matters — even though the DOM-insertion logic itself isn't covered
by an automated browser test.
"""
import json
from datetime import datetime, timezone
from models import SalesOrder, WorksOrder, BOMLine, Item


class TestAddComponentOfAssembly:
    _c = 0

    def _setup(self, session):
        TestAddComponentOfAssembly._c += 1
        c = TestAddComponentOfAssembly._c

        so = SalesOrder(so_number=f"SO-WOEDIT-{c:03d}", customer_name="Test Customer",
                         status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        assembly_item = Item(code=f"WOEDIT-ASM-{c}", description="Assembly Item",
                              qty_on_hand=50.0, avg_cost=10.0, active=True)
        replacement_item = Item(code=f"WOEDIT-REPL-{c}", description="Replacement Component",
                                 qty_on_hand=20.0, avg_cost=5.0, active=True)
        session.add_all([assembly_item, replacement_item])
        session.flush()

        wo = WorksOrder(wo_number=f"WO-WOEDIT-{c:03d}", so_id=so.id, order_type="ASSEMBLY",
                         status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()

        assembly_line = BOMLine(wo_id=wo.id, item_id=assembly_item.id, qty_required=1.0,
                                 unit_cost=10.0, line_type="ASSEMBLY_ITEM")
        session.add(assembly_line)
        session.commit()

        return {
            "so": so, "wo": wo,
            "assembly_item": assembly_item,
            "replacement_item": replacement_item,
            "assembly_line": assembly_line,
        }

    def test_added_component_nests_under_chosen_assembly(self, client, session):
        """Payload shaped as addItemFromCatalogue()/syncEditJSON() now produce
        when 'Add as component of [assembly]' is selected: the new item is
        nested inside the assembly's components array."""
        data = self._setup(session)
        wo = data["wo"]
        assembly_item = data["assembly_item"]
        replacement_item = data["replacement_item"]

        payload = [
            {
                "item_id": assembly_item.id,
                "qty_required": 1.0,
                "line_type": "ASSEMBLY_ITEM",
                "notes": "",
                "components": [
                    {
                        "item_id": replacement_item.id,
                        "qty_required": 2.0,
                        "notes": "",
                    }
                ],
            }
        ]

        resp = client.post(
            f"/works-orders/{wo.id}/edit",
            data={"bom_items_json": json.dumps(payload)},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        lines = BOMLine.query.filter_by(wo_id=wo.id).all()
        assembly_lines = [line for line in lines if line.line_type == "ASSEMBLY_ITEM"]
        component_lines = [line for line in lines if line.line_type == "COMPONENT"]

        assert len(assembly_lines) == 1
        assert len(component_lines) == 1

        new_component = component_lines[0]
        assert new_component.item_id == replacement_item.id
        # The critical assertion: nested under the assembly, not a new
        # top-level ASSEMBLY_ITEM/flat (parentless) line.
        assert new_component.parent_line_id == assembly_lines[0].id

    def test_edit_page_renders_assembly_target_select(self, client, session):
        """Smoke test: the edit page includes the new 'Add as component
        of…' select, defaulting to '— standalone item —'."""
        data = self._setup(session)
        wo = data["wo"]

        resp = client.get(f"/works-orders/{wo.id}/edit")
        body = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert 'id="assembly-target"' in body
        assert "standalone item" in body

    def test_standalone_add_still_produces_flat_line(self, client, session):
        """Leaving the selector on its default ('— standalone item —',
        empty value) must preserve today's flat-line behaviour — regression
        guard so the nesting fix doesn't change the common case."""
        data = self._setup(session)
        wo = data["wo"]
        assembly_item = data["assembly_item"]
        replacement_item = data["replacement_item"]

        payload = [
            {
                "item_id": assembly_item.id,
                "qty_required": 1.0,
                "line_type": "ASSEMBLY_ITEM",
                "notes": "",
            },
            {
                "item_id": replacement_item.id,
                "qty_required": 3.0,
                "line_type": "COMPONENT",
                "notes": "",
            },
        ]

        resp = client.post(
            f"/works-orders/{wo.id}/edit",
            data={"bom_items_json": json.dumps(payload)},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        lines = BOMLine.query.filter_by(wo_id=wo.id).all()
        standalone = next(line for line in lines if line.item_id == replacement_item.id)
        assert standalone.parent_line_id is None
