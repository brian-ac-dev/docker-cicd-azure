from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["APP_NAME"] = "PopShop"
    app.config["APP_VERSION"] = "1.1.0"
    app.config["USER_NAME"] = "Jean"
    app.config["USER_AVATAR_URL"] = "https://jemjaf.com/images/avatars/jean/0.png"
    app.config["SKOOL_COMMUNITY_URL"] = "https://skool.com/jemjaf"

    @app.context_processor
    def inject_user():
        return {
            "user_name": app.config["USER_NAME"],
            "user_avatar_url": app.config["USER_AVATAR_URL"],
            "skool_url": app.config["SKOOL_COMMUNITY_URL"],
        }

    from app.routes import bp

    app.register_blueprint(bp)
    return app
