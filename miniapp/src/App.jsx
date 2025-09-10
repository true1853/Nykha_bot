import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [user, setUser] = useState(null);
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      const tgUser = window.Telegram.WebApp.initDataUnsafe.user;
      setUser(tgUser);
    }
  }, []);

  const handleSend = () => {
    if (window.Telegram && window.Telegram.WebApp) {
      const payload = {
        action: "feedback",
        name: user?.first_name || "Гость",
        message,
      };
      window.Telegram.WebApp.sendData(JSON.stringify(payload));
      setSent(true);
      setTimeout(() => {
        window.Telegram.WebApp.close();
      }, 1500);
    }
  };

  return (
    <div className="tg-app">
      <h2>👋 {user ? `Привет, ${user.first_name}!` : "Привет!"}</h2>
      <p>Это мини-приложение Telegram.<br />Оставьте свой отзыв или вопрос:</p>
      <textarea
        placeholder="Ваше сообщение..."
        value={message}
        onChange={e => setMessage(e.target.value)}
        rows={4}
        disabled={sent}
      />
      <button
        className="send-btn"
        onClick={handleSend}
        disabled={!message.trim() || sent}
      >
        {sent ? "Отправлено!" : "Отправить в бота"}
      </button>
      <div className="footer">
        <small>Made for Telegram Mini Apps</small>
      </div>
    </div>
  );
}

export default App;
