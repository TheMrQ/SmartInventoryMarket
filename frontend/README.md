# Smart Inventory Market frontend

Responsive React/Vite operations dashboard for the FastAPI backend. It opens directly in thesis-demo mode; authentication is not implemented.

## Local run

Terminal 1, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` and `/health` to `http://127.0.0.1:8000` locally. For a deployed backend, set the optional safe `VITE_API_BASE_URL` in a local ignored `.env` file.

## Verification

```powershell
npm run lint
npm run build
```

The UI uses React Router, TanStack React Query, Lucide icons, Recharts, and Sonner. It contains dashboard, catalog, inventory, supplier mapping, purchase-order, sales/import, forecast, and inventory-decision/recommendation views. The frozen forecast model remains M5-specific; the UI presents that limitation instead of claiming arbitrary-SKU support.
