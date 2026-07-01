/**
 * API configuration for local dev, GitHub Pages, and production builds.
 */

declare global {
    interface Window {
        __API_BASE_URL__?: string;
    }
}

declare const process: {
    env: {
        API_BASE_URL?: string;
    };
};

const DEFAULT_API_BASE = '/api/v1';

function normalizeBaseUrl(url: string): string {
    return url.replace(/\/$/, '');
}

export function getApiBaseUrl(): string {
    if (typeof window !== 'undefined' && window.__API_BASE_URL__) {
        return normalizeBaseUrl(window.__API_BASE_URL__);
    }

    if (typeof process !== 'undefined' && process.env?.API_BASE_URL) {
        return normalizeBaseUrl(process.env.API_BASE_URL);
    }

    return DEFAULT_API_BASE;
}

export function apiUrl(path: string): string {
    const base = getApiBaseUrl();
    const suffix = path.replace(/^\/api\/v1\/?/, '').replace(/^\//, '');
    return suffix ? `${base}/${suffix}` : base;
}
