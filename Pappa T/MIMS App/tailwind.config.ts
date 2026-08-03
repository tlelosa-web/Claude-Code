import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: { DEFAULT: '#4361ee', dark: '#3f37c9' },
                success: { DEFAULT: '#10b981' },
                warning: { DEFAULT: '#f59e0b' },
                danger: { DEFAULT: '#ef4444' },
                navy: { DEFAULT: '#1d3557', light: '#2a4a70' },
                muted: '#6c757d',
            },
            fontFamily: {
                sans: ['Inter', 'ui-sans-serif', 'system-ui'],
            },
            boxShadow: {
                card: '0 4px 6px rgba(0,0,0,0.07)',
                dropdown: '0 8px 24px rgba(0,0,0,0.12)',
            },
            keyframes: {
                'slide-in': { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
                'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } },
            },
            animation: {
                'slide-in': 'slide-in 0.2s ease-out',
                'fade-in': 'fade-in 0.15s ease-out',
            },
        },
    },
    plugins: [],
}
export default config
