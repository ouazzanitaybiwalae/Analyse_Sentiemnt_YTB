// Après le déploiement (Phase 6), remplacez l'URL "cloud" par celle de votre Space.
// Format : https://<utilisateur>-<nom-du-space>.hf.space
const API_TARGETS = {
  cloud: "https://expert-rotary-phone-pjx5jxgp76rp29wqx-7860.app.github.dev",
  local: "http://localhost:8000",
};
const BATCH_SIZE = 200;       // commentaires par requête
const REQUEST_TIMEOUT = 60000; // ms (un Space "endormi" peut mettre du temps à se réveiller)
