/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./templates/**/*.html",
        "./**/*.py"
    ],
    theme: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
    ]

}
