// Content script : extrait les commentaires de la page YouTube.
if (!window.__ytSentimentLoaded) {
  window.__ytSentimentLoaded = true;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function collect(includeReplies) {
    const out = [];
    const seen = new Set();
    document.querySelectorAll("ytd-comments ytd-comment-thread-renderer #content-text").forEach((el) => {
      const text = (el.innerText || "").trim();
      if (!text) return;
      // Threads : une réponse vit dans ytd-comment-replies-renderer
      const isReply = !!el.closest("ytd-comment-replies-renderer");
      if (isReply && !includeReplies) return;
      const key = text + "|" + isReply;
      if (seen.has(key)) return;
      seen.add(key);
      out.push({ text, isReply });
    });
    return out;
  }

  // Commentaires dynamiques : YouTube ne charge que ~20 commentaires à la fois,
  // on fait défiler la page jusqu'à en avoir assez (ou jusqu'à stagnation).
  async function extract({ max = 100, includeReplies = false }) {
    const startY = window.scrollY;
    const comments = document.querySelector("ytd-comments");
    if (comments) comments.scrollIntoView({ behavior: "instant", block: "start" });

    let stagnant = 0, last = -1, list = collect(includeReplies);
    for (let i = 0; i < 40 && list.length < max && stagnant < 3; i++) {
      window.scrollTo(0, document.documentElement.scrollHeight);
      await sleep(700);
      list = collect(includeReplies);
      stagnant = list.length === last ? stagnant + 1 : 0;
      last = list.length;
    }
    window.scrollTo(0, startY);
    const title = document.querySelector("h1.ytd-watch-metadata, h1 yt-formatted-string")?.innerText?.trim() || document.title;
    return { title, comments: list.slice(0, max) };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type !== "EXTRACT_COMMENTS") return;
    extract(msg.options || {})
      .then((r) => sendResponse({ ok: true, ...r }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true; // réponse asynchrone
  });
}
