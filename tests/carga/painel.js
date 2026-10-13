// =============================================================================
// Teste de carga com k6 — o painel aguenta o início do semestre?
// -----------------------------------------------------------------------------
// "thresholds" funcionam como SLOs automatizados: se a latência p95 ou a taxa
// de erro passarem do limite, o k6 termina com erro e o pipeline FALHA.
// Os mesmos números aparecem nos alertas do Prometheus (deploy/base/alertas.yaml)
// e na análise do canary (deploy/base/analise-canary.yaml) — UM só conjunto de SLOs.
//
// Rodar local:  docker run --rm --network host -v "$PWD/tests/carga:/s" \
//                 -e BASE_URL=http://localhost:8000 grafana/k6:2.3.0 run /s/painel.js
// Customize: usuários (vus), duração e limites conforme o tamanho da IES.
// =============================================================================
import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const CURSOS = ["CC", "EC", "ES", "CD", "IA", "ADS"];

export const options = {
  scenarios: {
    pico_de_acesso: {
      executor: "ramping-vus",
      stages: [
        { duration: "20s", target: 20 }, // aquecimento
        { duration: "40s", target: 50 }, // pico (ex.: divulgação de resultados)
        { duration: "10s", target: 0 },  // desaceleração
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],                  // < 1% de erros
    http_req_duration: ["p(95)<500", "p(99)<1000"],  // latência em ms
    checks: ["rate>0.99"],
  },
};

export default function () {
  const curso = CURSOS[Math.floor(Math.random() * CURSOS.length)];
  const resposta = http.get(`${BASE_URL}/api/v1/cursos/${curso}/painel?periodo=2026.1`, {
    tags: { rota: "/api/v1/cursos/{curso}/painel" }, // agrupa métricas por rota, não por URL
  });
  check(resposta, {
    "status 200": (r) => r.status === 200,
    "painel com itens": (r) => r.json("itens").length > 0,
  });
  sleep(1);
}
