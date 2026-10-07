cd ~
cat > affiliate.js << 'JSEOF'
// ZER0 Updates — Amazon affiliate link auto-tagger
(function () {
    const AMAZON_TAG = "zer0updates-20";
    const AMAZON_HOSTS = ["amazon.com", "amazon.co.uk", "amazon.ca", "amazon.de", "amazon.fr", "amzn.to"];

    function isAmazonLink(href) {
        try {
            const url = new URL(href, window.location.href);
            return AMAZON_HOSTS.some(host => url.hostname.endsWith(host));
        } catch (e) {
            return false;
        }
    }

    function tagLink(a) {
        try {
            const url = new URL(a.href);
            url.searchParams.set("tag", AMAZON_TAG);
            a.href = url.toString();
            a.dataset.zer0Tagged = "1";
        } catch (e) {
            // skip malformed URLs
        }
    }

    function tagAllAmazonLinks(root) {
        const links = (root || document).querySelectorAll('a[href]');
        links.forEach(a => {
            if (a.dataset.zer0Tagged) return;
            if (isAmazonLink(a.href)) tagLink(a);
        });
    }

    // Tag links already on the page
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => tagAllAmazonLinks());
    } else {
        tagAllAmazonLinks();
    }

    // Also catch links added later (e.g. after deals.json loads and renders cards)
    const observer = new MutationObserver(() => tagAllAmazonLinks());
    observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
})();
JSEOF
