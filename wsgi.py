from app import create_app

app = create_app()

if __name__ == "__main__":
    from app.config import Config

    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=True,
    )
