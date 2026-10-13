output "enderecos" {
  description = "Endereços de acesso (porta 8080 mapeada pelo k3d)"
  value = {
    argocd     = "http://argocd.${var.dominio}:8080"
    grafana    = "http://grafana.${var.dominio}:8080"
    api_dev    = "http://kpi-dev.${var.dominio}:8080/docs"
    api_prod   = "http://kpi.${var.dominio}:8080/docs"
    senha_argo = "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
    senha_graf = "kubectl -n observabilidade get secret grafana -o jsonpath='{.data.admin-password}' | base64 -d"
  }
}
