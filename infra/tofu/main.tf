# =============================================================================
# Componentes da plataforma instalados via Helm.
#
#   Namespace          Componente            Etapa da trilha
#   -----------------  --------------------  -------------------------------
#   argocd             Argo CD               7  GitOps (CD)
#   argo-rollouts      Argo Rollouts         8  Canary com análise automática
#   kyverno            Kyverno               7  Políticas como código
#   observabilidade    kube-prometheus-stack 9  Métricas, alertas, Grafana
#   observabilidade    Loki + Alloy          9  Logs
#   observabilidade    Tempo                 9  Traces (OpenTelemetry)
#   chaos-mesh         Chaos Mesh            10 Engenharia do caos
#
# Depois do `tofu apply`, registre a aplicação no Argo CD:
#   kubectl apply -f deploy/argocd/
# =============================================================================

provider "kubernetes" {
  config_path    = pathexpand(var.kubeconfig)
  config_context = var.contexto
}

provider "helm" {
  kubernetes = {
    config_path    = pathexpand(var.kubeconfig)
    config_context = var.contexto
  }
}

locals {
  valores = "${path.module}/valores"
}

# ---------------------------------------------------------------------------
# GitOps
# ---------------------------------------------------------------------------
resource "helm_release" "argo_cd" {
  name             = "argo-cd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = var.versoes_charts["argo_cd"]
  namespace        = "argocd"
  create_namespace = true
  atomic           = true # se a instalação falhar, desfaz tudo (sem estado pela metade)
  timeout          = 600
  values = [templatefile("${local.valores}/argo-cd.yaml", {
    dominio = var.dominio
  })]
}

resource "helm_release" "argo_rollouts" {
  name             = "argo-rollouts"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-rollouts"
  version          = var.versoes_charts["argo_rollouts"]
  namespace        = "argo-rollouts"
  create_namespace = true
  atomic           = true
  timeout          = 600 # 1ª instalação baixa imagens: o padrão de 5 min é curto no WSL
  values = [templatefile("${local.valores}/argo-rollouts.yaml", {
    monitorar = var.habilitar_observabilidade
  })]
  # Com a observabilidade ligada, as CRDs do Prometheus Operator precisam existir
  # ANTES do ServiceMonitor do Rollouts. Com ela desligada, a dependência é inócua.
  depends_on = [helm_release.kube_prometheus_stack]
}

# ---------------------------------------------------------------------------
# Políticas como código (admission controller)
# ---------------------------------------------------------------------------
resource "helm_release" "kyverno" {
  name             = "kyverno"
  repository       = "https://kyverno.github.io/kyverno"
  chart            = "kyverno"
  version          = var.versoes_charts["kyverno"]
  namespace        = "kyverno"
  create_namespace = true
  atomic           = true
  timeout          = 600
  values           = [file("${local.valores}/kyverno.yaml")]
}

# ---------------------------------------------------------------------------
# Observabilidade
# ---------------------------------------------------------------------------
resource "helm_release" "kube_prometheus_stack" {
  count            = var.habilitar_observabilidade ? 1 : 0
  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = var.versoes_charts["kube_prometheus_stack"]
  namespace        = "observabilidade"
  create_namespace = true
  atomic           = true
  timeout          = 900
  values = [templatefile("${local.valores}/kube-prometheus-stack.yaml", {
    dominio = var.dominio
  })]
}

resource "helm_release" "loki" {
  count      = var.habilitar_observabilidade ? 1 : 0
  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  version    = var.versoes_charts["loki"]
  namespace  = "observabilidade"
  atomic     = true
  timeout    = 600
  values     = [file("${local.valores}/loki.yaml")]
  depends_on = [helm_release.kube_prometheus_stack]
}

resource "helm_release" "alloy" {
  count      = var.habilitar_observabilidade ? 1 : 0
  name       = "alloy"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "alloy"
  version    = var.versoes_charts["alloy"]
  namespace  = "observabilidade"
  atomic     = true
  timeout    = 600 # 1ª instalação baixa imagens: o padrão de 5 min é curto no WSL
  values     = [file("${local.valores}/alloy.yaml")]
  depends_on = [helm_release.loki]
}

resource "helm_release" "tempo" {
  count      = var.habilitar_observabilidade ? 1 : 0
  name       = "tempo"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "tempo"
  version    = var.versoes_charts["tempo"]
  namespace  = "observabilidade"
  atomic     = true
  timeout    = 600 # 1ª instalação baixa imagens: o padrão de 5 min é curto no WSL
  values     = [file("${local.valores}/tempo.yaml")]
  depends_on = [helm_release.kube_prometheus_stack]
}

# ---------------------------------------------------------------------------
# Engenharia do caos
# ---------------------------------------------------------------------------
resource "helm_release" "chaos_mesh" {
  count            = var.habilitar_caos ? 1 : 0
  name             = "chaos-mesh"
  repository       = "https://charts.chaos-mesh.org"
  chart            = "chaos-mesh"
  version          = var.versoes_charts["chaos_mesh"]
  namespace        = "chaos-mesh"
  create_namespace = true
  atomic           = true
  timeout          = 600
  values           = [file("${local.valores}/chaos-mesh.yaml")]
}

# Namespaces da aplicação com o rótulo que habilita as políticas Kyverno
# e o Pod Security Admission nativo do Kubernetes ("restricted").
resource "kubernetes_namespace_v1" "aplicacao" {
  for_each = toset(["kpi-dev", "kpi-prod"])
  metadata {
    name = each.key
    labels = {
      "app.kubernetes.io/part-of"                  = "kpi-academico"
      "pod-security.kubernetes.io/enforce"         = "restricted"
      "pod-security.kubernetes.io/enforce-version" = "latest"
    }
  }
}
