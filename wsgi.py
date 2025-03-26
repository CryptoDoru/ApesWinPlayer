from app import app

# This is a standard WSGI entry point
# Vercel can use this as a fallback if vercel_app doesn't work
if __name__ == "__main__":
    app.run()
