// Domínios exatos ou seus subdomínios; nunca aceitar nomes por substring.
const STORE_DOMAINS = ['mercadolivre.com.br','amazon.com.br','shopee.com.br','kabum.com.br','terabyteshop.com.br'];
function allowedOfferUrl(value) {
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443')) return '';
    const host = url.hostname.toLowerCase();
    return STORE_DOMAINS.some(domain => host === domain || host.endsWith('.'+domain)) ? url.href : '';
  } catch { return ''; }
}
function allowedOffer(record) { return Boolean(allowedOfferUrl(record?.url)); }
if (typeof module !== 'undefined') module.exports = {allowedOfferUrl, allowedOffer};
