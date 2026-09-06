# shadcndashboard Repository Conventions

Use this reference as a starting point, then verify against the checked-out repository because upstream may change.

## Known upstream conventions

The upstream project uses:

- React 19 + Vite
- TypeScript
- Tailwind CSS v4
- shadcn-style components
- React Router with central definitions in `src/routes/Router.tsx`
- lazy-loaded views wrapped by the repository's `Loadable` helper
- Recharts for charts
- SWR for data fetching
- MSW for mocked API responses
- npm / `package-lock.json`

There is no production backend in the base repository; mocked API handlers/data are used for demo data.

## Routing

Before adding routes, inspect `src/routes/Router.tsx`.

Follow the existing pattern:

1. lazy import the view
2. wrap it in the existing `Loadable`
3. add the route to the current router tree
4. use the existing full/blank layout split

Do not introduce another router instance.

## Layout

The main application shell lives under `src/layouts/full/` in the upstream structure.

Reuse its:

- sidebar
- header
- responsive shell
- theme integration

Do not recreate these as a second shell unless explicitly requested.

## Charts

Use Recharts. Do not add Chart.js, ECharts, ApexCharts, or another chart library unless the task needs a feature Recharts cannot reasonably provide.

## Icons

Prefer the icon packages already installed by the repository, such as Lucide React and Iconify.

## Data layer

Inspect existing `src/api/` structure before adding files.

When backend endpoints are unavailable:

- keep mock data in the repo's mock/data layer,
- expose it through MSW handlers,
- fetch it through the same mechanism pages will use for a real backend.

Do not embed large fake datasets directly in page components.

## Validation

Run:

```bash
npm run lint
npm run build
```

The build includes TypeScript validation in the upstream project, so TypeScript errors are completion blockers.
