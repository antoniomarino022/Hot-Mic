import hashlib
import hmac
import time
import unittest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from config.database import get_session
from config.settings import settings
from main import app
import src.models  # noqa: F401

# In-memory SQLite engine for tests
sqlite_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_test_session():
    with Session(sqlite_engine) as session:
        yield session


# Override session dependency
app.dependency_overrides[get_session] = get_test_session


class TestRegisterAndAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SQLModel.metadata.create_all(sqlite_engine)
        cls.client = TestClient(app, raise_server_exceptions=True)

    @classmethod
    def tearDownClass(cls):
        SQLModel.metadata.drop_all(sqlite_engine)

    def test_1_register_page_html(self):
        """Verifica che la pagina /register venga renderizzata con la UI Telegram."""
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)
        html = response.text
        # Verifica inclusione libreria Telegram UI
        self.assertIn("@telegram-apps/telegram-ui", html)
        # Verifica inclusione SDK Telegram WebApp
        self.assertIn("telegram-web-app.js", html)
        # Verifica inclusione Telegram Login Widget
        self.assertIn("telegram-widget.js", html)
        # Verifica elementi chiave UI
        self.assertIn("Hot-Mic", html)
        self.assertIn("Confessioni anonime", html)

    def test_2_widget_auth_flow(self):
        """Verifica l'autenticazione tramite Telegram Login Widget con firma valida HMAC e cookie di sessione."""
        bot_token = settings.TELEGRAM_BOT_TOKEN.get_secret_value() or "test_token_123"

        telegram_id = 987654321
        auth_date = int(time.time())

        # Costruisci data check string secondo specifiche Telegram
        fields = {
            "auth_date": str(auth_date),
            "first_name": "Mario",
            "id": str(telegram_id),
            "username": "mariorossi",
        }
        sorted_items = sorted(fields.items())
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

        # Secret key = sha256(bot_token)
        secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
        valid_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        widget_payload = {
            "id": telegram_id,
            "first_name": "Mario",
            "username": "mariorossi",
            "auth_date": auth_date,
            "hash": valid_hash,
            "referral_code": None,
            "accepted": True,
        }

        res = self.client.post("/auth/widget", json=widget_payload)
        self.assertEqual(res.status_code, 201)
        user_data = res.json()
        self.assertEqual(user_data["coins_balance"], 50)
        self.assertIsInstance(user_data["id"], int)
        self.assertIn("user_key", user_data)
        # Zero-PII: telegram_id NON deve apparire nella risposta
        self.assertNotIn("telegram_id", user_data)
        # Cookie di sessione impostato
        self.assertIn("hotmic_session", res.cookies)

        # Con il cookie di sessione, la pagina mostra il profilo autenticato
        session_cookie = res.cookies["hotmic_session"]
        res_page = self.client.get("/register", cookies={"hotmic_session": session_cookie})
        self.assertEqual(res_page.status_code, 200)
        self.assertIn("Sei connesso", res_page.text)

    def test_3_confession_crud_with_autoincrement_id(self):
        """Verifica creazione ed eliminazione confessione con PK autoincrement integer e senza categoria."""
        # 1. Login user
        bot_token = settings.TELEGRAM_BOT_TOKEN.get_secret_value() or "test_token_123"
        telegram_id = 1122334455
        auth_date = int(time.time())
        fields = {"auth_date": str(auth_date), "id": str(telegram_id)}
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
        secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
        valid_hash = hmac.new(secret_key, data_check.encode("utf-8"), hashlib.sha256).hexdigest()

        auth_res = self.client.post("/auth/widget", json={
            "id": telegram_id,
            "auth_date": auth_date,
            "hash": valid_hash,
            "accepted": True,
        })
        self.assertEqual(auth_res.status_code, 201)
        cookie = auth_res.cookies["hotmic_session"]

        # 2. Crea confessione
        confession_payload = {
            "content": "Questa è una confessione anonima di prova!",
            "poll_option_a": "D'accordo",
            "poll_option_b": "In disaccordo",
        }
        res_post = self.client.post(
            "/confessions/",
            json=confession_payload,
            cookies={"hotmic_session": cookie},
        )
        self.assertEqual(res_post.status_code, 201)
        data = res_post.json()
        
        # Verifica che l'ID sia un intero autoincrement
        self.assertIsInstance(data["id"], int)
        self.assertIsInstance(data["author_id"], int)
        self.assertGreater(data["id"], 0)
        # Verifica che 'category' NON sia presente nello schema
        self.assertNotIn("category", data)

        # 3. Elimina la confessione
        confession_id = data["id"]
        res_del = self.client.delete(
            f"/confessions/{confession_id}",
            cookies={"hotmic_session": cookie},
        )
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(res_del.json()["status"], "ok")

        # 4. Eliminando di nuovo, deve restituire 404
        res_del_again = self.client.delete(
            f"/confessions/{confession_id}",
            cookies={"hotmic_session": cookie},
        )
        self.assertEqual(res_del_again.status_code, 404)

    def test_4_logout(self):
        """Verifica la disconnessione e pulizia del cookie."""
        res = self.client.post("/auth/logout")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
