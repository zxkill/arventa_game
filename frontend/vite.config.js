import {defineConfig} from 'vite';

export default defineConfig({
    root: './app',
    build: {
        outDir: '../dist',
        minify: true,
        watch: {}, // Включаем режим watch
        emptyOutDir: true,
        rollupOptions: {
            input: {
                index: '/index.html',
                game: '/game.html',
            },
            output: {
                manualChunks: undefined,
            },
        },
    },
    publicDir: 'public',
    server: {
        port: 5173,
        watch: {
            usePolling: true,
        },
    },
});
