"""Tests for routes/items.py — Edit Item (identity/pricing) route.

See docs/specs/item-edit-and-levels-popup.md.
"""
from models import db, Item


class TestUpdateItem:
    _counter = 0

    def _next_code(self):
        TestUpdateItem._counter += 1
        return f"EDIT-ITEM-TEST-{TestUpdateItem._counter:03d}"

    def test_update_item_success_updates_all_fields(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Original description",
                    category="Old Category", active=True, last_cost=1.0, avg_cost=1.5,
                    excl_price=2.0, incl_price=2.3, qty_on_hand=10.0)
        session.add(item)
        session.commit()

        new_code = self._next_code()
        response = client.post(f'/items/{item.id}/edit', data={
            'code': new_code,
            'description': 'Updated description',
            'category': 'New Category',
            'active': 'on',
            'last_cost': '5.5',
            'avg_cost': '6.25',
            'excl_price': '10.0',
            'incl_price': '11.5',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "updated" in response.get_data(as_text=True)

        db.session.refresh(item)
        assert item.code == new_code
        assert item.description == 'Updated description'
        assert item.category == 'New Category'
        assert item.active is True
        assert item.last_cost == 5.5
        assert item.avg_cost == 6.25
        assert item.excl_price == 10.0
        assert item.incl_price == 11.5
        # Qty on Hand must never be touched by this route.
        assert item.qty_on_hand == 10.0

    def test_update_item_inactive_checkbox_unchecked(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Desc", active=True)
        session.add(item)
        session.commit()

        # Unchecked checkboxes are simply absent from the posted form data.
        response = client.post(f'/items/{item.id}/edit', data={
            'code': item.code,
            'description': 'Desc',
            'category': '',
            'last_cost': '0',
            'avg_cost': '0',
            'excl_price': '0',
            'incl_price': '0',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(item)
        assert item.active is False

    def test_update_item_rejects_duplicate_code(self, app, db, session, client):
        code_a = self._next_code()
        code_b = self._next_code()
        item_a = Item(code=code_a, description="Item A", active=True)
        item_b = Item(code=code_b, description="Item B", active=True,
                      last_cost=1.0, avg_cost=1.0, excl_price=1.0, incl_price=1.0)
        session.add_all([item_a, item_b])
        session.commit()
        item_b_id = item_b.id

        response = client.post(f'/items/{item_b_id}/edit', data={
            'code': code_a,  # already used by item_a
            'description': 'Attempted rename',
            'category': '',
            'last_cost': '9.0',
            'avg_cost': '9.0',
            'excl_price': '9.0',
            'incl_price': '9.0',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "already in use" in response.get_data(as_text=True)

        # No changes persisted.
        unchanged = db.session.get(Item, item_b_id)
        assert unchanged.code == code_b
        assert unchanged.description == 'Item B'
        assert unchanged.last_cost == 1.0

    def test_update_item_rejects_invalid_numeric_input(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Desc", active=True,
                    last_cost=1.0, avg_cost=1.0, excl_price=1.0, incl_price=1.0)
        session.add(item)
        session.commit()
        item_id = item.id

        response = client.post(f'/items/{item_id}/edit', data={
            'code': item.code,
            'description': 'Desc',
            'category': '',
            'last_cost': 'not-a-number',
            'avg_cost': '1.0',
            'excl_price': '1.0',
            'incl_price': '1.0',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "must be numbers" in response.get_data(as_text=True)

        unchanged = db.session.get(Item, item_id)
        assert unchanged.last_cost == 1.0

    def test_update_item_rejects_blank_code(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Desc", active=True)
        session.add(item)
        session.commit()
        item_id = item.id
        original_code = item.code

        response = client.post(f'/items/{item_id}/edit', data={
            'code': '   ',
            'description': 'Desc',
            'category': '',
            'last_cost': '0',
            'avg_cost': '0',
            'excl_price': '0',
            'incl_price': '0',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "cannot be blank" in response.get_data(as_text=True)

        unchanged = db.session.get(Item, item_id)
        assert unchanged.code == original_code
