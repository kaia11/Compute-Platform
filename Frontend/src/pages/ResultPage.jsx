import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import HeaderUserSection from "../components/layout/HeaderUserSection";
import PageShell from "../components/layout/PageShell";
import { cancelRental, getRentalDetail } from "../services/api";
import { formatCurrency, formatDuration } from "../utils/formatters";

export default function ResultPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const rentalId = searchParams.get("rentalId");
  const [rental, setRental] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (!rentalId) {
      setError("缺少 rentalId");
      setLoading(false);
      return;
    }
    let active = true;
    getRentalDetail(rentalId)
      .then((data) => {
        if (active) {
          setRental(data);
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
  }, [rentalId]);

  async function handleCancelRental() {
    if (!rentalId) {
      return;
    }
    setCancelling(true);
    setError("");
    try {
      const result = await cancelRental(rentalId);
      setRental((current) => (current ? { ...current, ...result, status: result.status } : current));
    } catch (err) {
      setError(err.message);
    } finally {
      setCancelling(false);
    }
  }

  if (!rentalId) {
    return <Navigate to="/catalog" replace />;
  }

  return (
    <PageShell compact>
      <header className="standard-header">
        <div>
          <span className="eyebrow">Rental Result</span>
          <h1>连接信息与分配结果</h1>
          <p>创建租单后即可查看已分配机柜、小时成本、总时长与取消租用状态。</p>
        </div>
        <div className="header-action-group">
          <Link className="secondary-link" to="/catalog">
            返回卡型页
          </Link>
          <HeaderUserSection />
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <div className="empty-state">正在加载租单详情...</div> : null}

      {!loading && rental ? (
        <section className="result-layout">
          <div className="panel result-primary">
            <div className="panel-head">
              <div>
                <h2>{rental.card_type} / {rental.cabinet_type}</h2>
                <p>租用台数 {rental.cabinet_count}，当前状态 {rental.status}</p>
              </div>
              <button
                className="primary-action"
                disabled={cancelling || rental.status === "cancelled"}
                onClick={handleCancelRental}
              >
                {rental.status === "cancelled" ? "已取消" : cancelling ? "处理中..." : "取消租用"}
              </button>
            </div>

            <div className="result-stat-grid">
              <div><span>开始时间</span><strong>{rental.started_at ?? "-"}</strong></div>
              <div><span>结束时间</span><strong>{rental.ended_at ?? "-"}</strong></div>
              <div><span>总时长</span><strong>{formatDuration(rental.duration_seconds)}</strong></div>
              <div><span>时段</span><strong>{rental.timeslot}</strong></div>
              <div><span>用户每小时总价</span><strong>{formatCurrency(rental.hourly_user_price_total)}</strong></div>
              <div><span>电费每小时总成本</span><strong>{formatCurrency(rental.hourly_power_cost_total)}</strong></div>
              <div><span>用户总金额</span><strong>{formatCurrency(rental.user_total_amount)}</strong></div>
              <div><span>电费总成本</span><strong>{formatCurrency(rental.power_cost_total)}</strong></div>
            </div>

            <div className="allocation-list">
              {rental.allocations.map((item) => (
                <article key={item.cabinet_code} className="allocation-card">
                  <div>
                    <h3>{item.cabinet_code}</h3>
                    <p>{item.location} · {item.cabinet_type}</p>
                  </div>
                  <div className="allocation-metrics">
                    <span>容量 {item.capacity_cards} 卡</span>
                    <span>用户每小时 {formatCurrency(item.hourly_user_price)}</span>
                    <span>电费每小时 {formatCurrency(item.hourly_power_cost)}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel result-side">
            <h3>连接信息</h3>
            <div className="credential-block">
              <span>IP</span>
              <strong>{rental.connection?.ip ?? "-"}</strong>
            </div>
            <div className="credential-block">
              <span>Password</span>
              <strong>{rental.connection?.password ?? "-"}</strong>
            </div>
            <button className="secondary-link secondary-link-block" onClick={() => navigate("/")}>
              回到封面页
            </button>
          </div>
        </section>
      ) : null}
    </PageShell>
  );
}
