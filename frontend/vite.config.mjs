import { defineConfig } from 'vite';

const pageRoutes = new Set([
  '/login',
  '/register',
  '/portal',
  '/portal/detail',
  '/member',
  '/member/catalog',
  '/member/detail',
  '/member/loans-page',
  '/member/reservations-page',
  '/member/notifications-page',
  '/admin/portal',
  '/admin/members-page',
  '/admin/books-page',
  '/admin/copies-page',
  '/admin/circulation-page',
  '/admin/fines-page',
  '/admin/auditlogs-page',
  '/admin/reminder-policy-page',
  '/admin/reports-page',
  '/admin/users-page',
  '/admin/announcements-page',
]);

function cleanUrlRedirect() {
  return (req, res, next) => {
    if (!req.url) {
      next();
      return;
    }

    const [pathname, query = ''] = req.url.split('?');
    if (!pageRoutes.has(pathname)) {
      next();
      return;
    }

    res.statusCode = 302;
    res.setHeader('Location', `${pathname}/${query ? `?${query}` : ''}`);
    res.end();
  };
}

export default defineConfig({
  plugins: [
    {
      name: 'library-clean-url-redirect',
      configureServer(server) {
        server.middlewares.use(cleanUrlRedirect());
      },
      configurePreviewServer(server) {
        server.middlewares.use(cleanUrlRedirect());
      },
    },
  ],
  server: {
    host: 'localhost',
    port: 23124,
  },
  preview: {
    host: 'localhost',
    port: 24124,
  },
});
