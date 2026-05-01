import { useEffect, useState } from "react";

export default function CatalogCard({ card, onSubmit, submitting }) {
  const [cabinetType, setCabinetType] = useState(card.card_type === "4090" ? "单卡机柜" : card.cabinet_desc);
  const [cardCount, setCardCount] = useState(1);
  const [pricingOpen, setPricingOpen] = useState(false);

  useEffect(() => {
    if (card.card_type === "4090") {
      return;
    }
    setCabinetType(card.cabinet_desc);
  }, [card]);

  const selectedPricing =
    card.pricing_options?.find((item) => item.cabinet_type === cabinetType)?.pricing_preview ??
    card.pricing_options?.[0]?.pricing_preview ??
    [];
  const maxCardCount = selectedPricing[selectedPricing.length - 1]?.card_count ?? 1;

  useEffect(() => {
    setCardCount((current) => Math.min(current, maxCardCount));
  }, [maxCardCount]);

  useEffect(() => {
    setPricingOpen(false);
  }, [cabinetType]);

  return (
    <article className="catalog-card">
      <div className="catalog-card-head">
        <div className="catalog-card-head-top">
          <div>
            <span className="eyebrow">{card.card_type === "4090" ? "灵活配卡" : "按卡租用"}</span>
            <h3>{card.title}</h3>
          </div>
          <button
            className="primary-action catalog-card-submit"
            disabled={submitting}
            onClick={() =>
              onSubmit(card.card_type, {
                card_type: card.card_type,
                cabinet_type: cabinetType,
                card_count: cardCount
              })
            }
          >
            {submitting ? "提交中..." : "立即使用"}
          </button>
        </div>
        <p>{card.cabinet_desc}</p>
      </div>

      <div className="spec-list">
        <div><span>显存</span><strong>{card.vram}</strong></div>
        <div><span>CPU</span><strong>{card.cpu}</strong></div>
        <div><span>内存</span><strong>{card.memory}</strong></div>
      </div>

      <div className="card-form">
        {card.card_type === "4090" ? (
          <label className="field">
            <span>机柜类型</span>
            <select value={cabinetType} onChange={(event) => setCabinetType(event.target.value)}>
              <option value="单卡机柜">单卡机柜</option>
              <option value="双卡机柜">双卡机柜</option>
            </select>
          </label>
        ) : null}

        <label className="field">
          <span>租几张卡</span>
          <input
            type="number"
            min="1"
            max={maxCardCount}
            value={cardCount}
            onChange={(event) => {
              const nextValue = Number(event.target.value) || 1;
              setCardCount(Math.min(Math.max(nextValue, 1), maxCardCount));
            }}
          />
        </label>
      </div>

      <div className="pricing-dropdown">
        <button
          type="button"
          className="pricing-dropdown-trigger"
          onClick={() => setPricingOpen((current) => !current)}
        >
          <span>查看每张卡价位</span>
          <strong>{pricingOpen ? "收起" : `${selectedPricing.length}档价格`}</strong>
        </button>
        {pricingOpen ? (
          <div className="pricing-preview">
            {selectedPricing.map((tier) => (
              <div key={`${cabinetType}-${tier.card_count}`} className="pricing-preview-row">
                <span>{tier.card_count}卡</span>
                <strong>{tier.hourly_user_price_total.toFixed(1)}元/小时</strong>
                <em>均价 {tier.avg_per_card.toFixed(2)}/卡</em>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="catalog-card-foot">
        <div>
          <span className="price-label">展示价格</span>
          <strong>{selectedPricing[0] ? `${selectedPricing[0].card_count}卡 ${selectedPricing[0].hourly_user_price_total.toFixed(1)}元/小时起` : card.display_price}</strong>
        </div>
      </div>
    </article>
  );
}
