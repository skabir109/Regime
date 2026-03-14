# FINAL DEPLOYMENT INSTRUCTIONS: Regime Full-Stack

Follow these exact steps to get your hackathon demo live on DigitalOcean.

## 1. Preparation (GitHub)
Ensure all latest changes (SQLModel, Next.js, Documentation, Security) are pushed to your GitHub repository.
```bash
git add .
git commit -m "Final polish: Intelligence, Security, and Production Infrastructure"
git push origin main
```

## 2. DigitalOcean Setup
1.  **Log in** to your DigitalOcean account.
2.  Click **"Create"** (top right) -> **"Apps"**.
3.  Choose **GitHub** as the source.
4.  Select your `regime` repository and the `main` branch.
5.  **CRITICAL:** Look for the link that says **"Edit Plan"** or **"Upload App Spec"**. 
6.  Upload the `app.yaml` file located in your project root. DigitalOcean will automatically configure the `regime-api` and `regime-web` services.

## 3. Environment Variables (The "Secrets")
DigitalOcean will ask you to provide values for the following. Copy these from your DigitalOcean managed database and your local `.env`:

### For `regime-api` (Backend):
*   `DATABASE_URL`: Your DigitalOcean PostgreSQL runtime connection string.
*   `DIRECT_URL`: Your DigitalOcean PostgreSQL direct connection string.
*   `LLM_API_KEY`: Your custom agent key or OpenAI key.
*   `FRONTEND_ORIGIN`: Set this to `${regime-web.PUBLIC_URL}` (DigitalOcean will resolve this automatically).

### For `regime-web` (Frontend):
*   `NEXT_PUBLIC_API_BASE_URL`: Set this to `${regime-api.PUBLIC_URL}` (This tells the Next.js app where the backend lives).

## 4. Post-Deployment "CORS" Fix
Once the app is live, DigitalOcean will give you a public URL for your frontend (e.g., `https://regime-web-abcde.ondigitalocean.app`).
1.  Go to the **App Settings** in DigitalOcean.
2.  Select the `regime-api` component.
3.  Ensure the `CORS_ORIGINS` environment variable contains your public frontend URL.

## 5. Deployment Verification
1.  **Check Tables:** Since `SQLModel.metadata.create_all()` is in the startup code, your DigitalOcean PostgreSQL tables will be created automatically the moment the backend starts.
2.  **Test Docs:** Visit `your-url.app/docs` to ensure the guide is loading.
3.  **Check Terminal:** Log in and ensure the "Strategic Executive Summary" is being generated.

---

## Technical Support / Troubleshooting
*   **Build Failure?** Check the "Logs" tab in DigitalOcean. It usually means a missing dependency in `requirements.txt` or `package.json`. (I've already verified these, so it should be smooth).
*   **Database Error?** Ensure the backend is using the DigitalOcean managed database connection strings you configured in App Platform, and verify inbound trusted sources/network settings on the database cluster.
