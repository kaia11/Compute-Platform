import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import CatalogCard from "../components/catalog/CatalogCard";
import HeaderUserSection from "../components/layout/HeaderUserSection";
import PageShell from "../components/layout/PageShell";
import { createRental, getCards } from "../services/api";

export default function CatalogPage() {
  const navigate = useNavigate();
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    getCards()
      .then((data) => {
        if (active) {
          setCards(data.items ?? []);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleCreateRental(payload) {
    setSubmitting(true);
    setError("");
    try {
      const result = await createRental(payload);
      navigate(`/result?rentalId=${result.rental_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell compact>
      <header className="standard-header">
        <div>
          <span className="eyebrow">Choose Compute</span>
          <h1>按需选择你的算力卡型</h1>
          <p>整机柜租赁模式下，前端只负责传递卡型、机柜类型、时段和租用台数。</p>
        </div>
        <div className="header-action-group">
          <Link className="secondary-link" to="/">
            返回封面页
          </Link>
          <HeaderUserSection />
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      {loading ? (
        <div className="empty-state">正在加载卡型信息...</div>
      ) : (
        <section className="catalog-grid">
          {cards.map((card) => (
            <CatalogCard
              key={card.card_type}
              card={card}
              onSubmit={handleCreateRental}
              submitting={submitting}
            />
          ))}
        </section>
      )}
    </PageShell>
  );
}
