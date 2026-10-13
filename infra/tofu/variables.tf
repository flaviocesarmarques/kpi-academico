# Variáveis da plataforma. Sobrescreva em terraform.tfvars (veja o .exemplo).
# Cada componente pode ser ligado/desligado — útil em máquinas com pouca RAM.

variable "kubeconfig" {
  description = "Caminho do kubeconfig"
  type        = string
  default     = "~/.kube/config"
}

variable "contexto" {
  description = "Contexto do kubeconfig (o k3d cria k3d-<nome-do-cluster>)"
  type        = string
  default     = "k3d-kpi"
}

variable "dominio" {
  description = "Domínio base dos Ingress (*.localhost resolve para 127.0.0.1)"
  type        = string
  default     = "localhost"
}

variable "habilitar_observabilidade" {
  description = "Prometheus, Grafana, Alertmanager, Loki, Alloy e Tempo"
  type        = bool
  default     = true
}

variable "habilitar_caos" {
  description = "Chaos Mesh (engenharia do caos)"
  type        = bool
  default     = true
}

variable "versoes_charts" {
  description = "Versões FIXAS dos Helm charts (atualize de forma consciente, via PR)"
  type        = map(string)
  default = {
    argo_cd               = "10.10.3"
    argo_rollouts         = "2.43.6"
    kyverno               = "3.9.1"
    kube_prometheus_stack = "92.3.0"
    loki                  = "7.3.0"
    alloy                 = "1.13.1"
    tempo                 = "1.24.4"
    chaos_mesh            = "2.8.4"
  }
}
