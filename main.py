"""Lance l'équipe d'agents Fusée et son tableau de bord : python main.py"""
import asyncio
import os
import sys
import threading
import webbrowser

import uvicorn

from fusee_agents.config import PORT

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("ANTHROPIC_AUTH_TOKEN"):
        print("⚠️  ANTHROPIC_API_KEY manquante : copie .env.example en .env et mets ta clé.", file=sys.stderr)
    print(f"🚀 Fusée démarre — application sur http://localhost:{PORT}")
    if os.getenv("OPEN_BROWSER", "true").lower() in ("1", "true", "oui", "yes"):
        threading.Timer(2.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    # Par défaut, Fusée n'est accessible que depuis ce Mac (HOST=127.0.0.1).
    # HOST=0.0.0.0 l'ouvre aux autres appareils du Wi-Fi (téléphone) : mets alors un mot de passe d'appli.
    host = os.getenv("HOST", "127.0.0.1").strip() or "127.0.0.1"
    if host not in ("127.0.0.1", "::1", "localhost") and not os.getenv("DASHBOARD_PASSWORD", "").strip():
        print("🔒 HOST ouvre Fusée aux autres appareils, mais il n'y a pas de mot de passe : Fusée reste fermée à "
              "ce Mac. Mets un mot de passe (⚙️ Réglages → 📱 Fusée sur ton iPhone).", file=sys.stderr)
        host = "127.0.0.1"
    elif host != "127.0.0.1":
        print(f"📶 Fusée est aussi ouverte aux appareils du Wi-Fi (port {PORT}), avec mot de passe.")
    # Second petit serveur, uniquement pour le public (chat des sites, statistiques, désinscription) :
    # c'est LUI, et lui seul, qu'on expose sur internet (tailscale funnel). L'appli reste privée.
    public_port = int(os.getenv("PUBLIC_PORT", "8001"))

    async def serve() -> None:
        servers = [uvicorn.Server(uvicorn.Config("fusee_agents.web:app", host=host, port=PORT, log_level="warning")),
                   uvicorn.Server(uvicorn.Config("fusee_agents.web:public_app", host="127.0.0.1", port=public_port,
                                                 log_level="warning"))]
        await asyncio.gather(*(s.serve() for s in servers))

    asyncio.run(serve())
