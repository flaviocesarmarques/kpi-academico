# =============================================================================
# OpenTofu — plataforma do cluster como código (etapa 6)
# -----------------------------------------------------------------------------
# OpenTofu é o fork livre (licença MPL, Linux Foundation) do Terraform, criado
# após a mudança deste para a licença BSL. Sintaxe HCL compatível.
#
# Boas práticas:
#   • Versões de OpenTofu e dos provedores FIXADAS (o .terraform.lock.hcl,
#     gerado no primeiro `tofu init`, deve ser COMMITADO).
#   • ESTADO: aqui é local (laboratório). Em equipe, use backend remoto com
#     travamento (ex.: backend "pg" em PostgreSQL, ou S3 compatível).
#   • CRIPTOGRAFIA DO ESTADO (recurso exclusivo do OpenTofu). O estado contém
#     segredos; criptografe-o definindo a variável de ambiente antes do init:
#       export TF_ENCRYPTION='key_provider "pbkdf2" "k" { passphrase = "<frase longa>" }
#         method "aes_gcm" "m" { keys = key_provider.pbkdf2.k }
#         state { method = method.aes_gcm.m }'
#   • Sempre `tofu plan` e revise antes de `tofu apply`.
# =============================================================================
terraform {
  required_version = ">= 1.13.0"

  required_providers {
    # O registro do OpenTofu (registry.opentofu.org) espelha estes provedores.
    helm = {
      source  = "hashicorp/helm"
      version = "~> 3.3"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 3.3"
    }
  }
}
