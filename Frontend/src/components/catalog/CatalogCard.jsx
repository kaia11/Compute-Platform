import { useEffect, useState } from "react";

export default function CatalogCard({ card, onSubmit, submitting }) {
  const [timeslot, setTimeslot] = useState("day");
  const [cabinetType, setCabinetType] = useState(card.card_type === "4090" ? "单卡机柜" : card.cabinet_desc);
  const [cabinetCount, setCabinetCount] = useState(1);

  useEffect(() => {
    if (card.card_type === "4090") {
      return;
    }
    setCabinetType(card.cabinet_desc);
  }, [card]);

  return (
    <article className="catalog-card">
      <div className="catalog-card-head">
        <span className="eyebrow">{card.card_type === "4090" ? "灵活配置" : "整机柜"}</span>
        <h3>{card.title}</h3>
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
          <span>时段</span>
          <select value={timeslot} onChange={(event) => setTimeslot(event.target.value)}>
            <option value="day">白天</option>
            <option value="night">夜晚</option>
          </select>
        </label>

        <label className="field">
          <span>租几台</span>
          <input
            type="number"
            min="1"
            value={cabinetCount}
            onChange={(event) => setCabinetCount(Number(event.target.value) || 1)}
          />
        </label>
      </div>

      <div className="catalog-card-foot">
        <div>
          <span className="price-label">展示价格</span>
          <strong>{card.display_price}</strong>
        </div>
        <button
          className="primary-action"
          disabled={submitting}
          onClick={() =>
            onSubmit({
              card_type: card.card_type,
              cabinet_type: cabinetType,
              cabinet_count: cabinetCount,
              timeslot
            })
          }
        >
          {submitting ? "提交中..." : "立即使用"}
        </button>
      </div>
    </article>
  );
}
