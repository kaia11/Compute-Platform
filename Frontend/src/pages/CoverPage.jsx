import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import HeaderUserSection from "../components/layout/HeaderUserSection";
import PageShell from "../components/layout/PageShell";
import NetworkGraph from "../components/cover/NetworkGraph";
import { useAuth } from "../context/AuthContext";
import { API_BASE_URL, getLocationsSummary } from "../services/api";

export default function CoverPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getLocationsSummary()
      .then((data) => {
        if (active) {
          setSummary(data);
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

  return (
    <PageShell>
      <header className="hero-header">
        <div>
          <span className="eyebrow">Compute Rental Network</span>
          <h1>整机柜算力网络</h1>
          <p className="hero-copy">
            实时展示四个位置的机柜分布与可用状态。绿色表示当前仍有可租机柜，红色表示已占满，灰色表示离线省电中。
          </p>
        </div>
        <div className="header-action-group">
          <button className="primary-action" onClick={() => navigate(isAuthenticated ? "/catalog" : "/auth")}>
            立即租赁
          </button>
          <HeaderUserSection />
        </div>
      </header>

      <section className="cover-content">
        <div className="panel panel-network">
          <div className="panel-head">
            <div>
              <h2>可用机柜</h2>
              <p>移动到任意位置节点上，查看该位置内部不同机柜类型的剩余台数。</p>
            </div>
            <div className="legend">
              <span className="legend-chip legend-available">有卡</span>
              <span className="legend-chip legend-rented">塞满</span>
              <span className="legend-chip legend-offline">离线</span>
            </div>
          </div>

          {loading ? <div className="empty-state">正在加载位置数据...</div> : null}
          {error ? <div className="error-banner">{error}</div> : null}
          {!loading && !error ? <NetworkGraph summary={summary} /> : null}
        </div>

        <div className="panel panel-side">
          <h3>接口来源</h3>
          <p>封面页节点与 hover 明细统一来自后端位置聚合接口，前端不做本地拼装。</p>
          <code>{API_BASE_URL}/api/locations/summary</code>
          <div className="side-links">
            <Link className="secondary-link" to={isAuthenticated ? "/catalog" : "/auth"}>
              进入卡型选择页
            </Link>
          </div>
        </div>
      </section>
    </PageShell>
  );
}
