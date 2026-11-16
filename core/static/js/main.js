document.addEventListener("DOMContentLoaded", () => {
  initHeroSlider();
  initAOS();
  initCounters();
  initStickyHeader();
  initSmoothScroll();
  initLightbox();
  initBackToTop();
});

/* ===== Hero slider ===== */
function initHeroSlider() {
  const slides = document.querySelectorAll(".hero-slide");
  if (slides.length < 2) return;

  const dotsContainer = document.getElementById("heroDots");
  let current = 0;
  let timer = null;
  const interval = (window.HERO_SLIDER_INTERVAL || 6) * 1000;

  slides.forEach((_, i) => {
    const dot = document.createElement("button");
    dot.setAttribute("aria-label", `Slide ${i + 1}`);
    if (i === 0) dot.classList.add("active");
    dot.addEventListener("click", () => goTo(i));
    dotsContainer.appendChild(dot);
  });

  const dots = dotsContainer.querySelectorAll("button");

  function goTo(index) {
    slides[current].classList.remove("active");
    dots[current].classList.remove("active");
    current = (index + slides.length) % slides.length;
    slides[current].classList.add("active");
    dots[current].classList.add("active");
    restart();
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  function restart() {
    clearInterval(timer);
    timer = setInterval(next, interval);
  }

  document.getElementById("heroNext")?.addEventListener("click", next);
  document.getElementById("heroPrev")?.addEventListener("click", prev);

  restart();
}

/* ===== AOS (animations au scroll) ===== */
function initAOS() {
  if (window.AOS) {
    AOS.init({ duration: 800, once: true, offset: 80 });
  }
}

/* ===== Compteurs statistiques ===== */
function initCounters() {
  const counters = document.querySelectorAll(".stat-number");
  if (!counters.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.dataset.count || "0", 10);
        const duration = 1600;
        const start = performance.now();

        function tick(now) {
          const progress = Math.min((now - start) / duration, 1);
          el.textContent = Math.floor(progress * target).toLocaleString("fr-FR");
          if (progress < 1) requestAnimationFrame(tick);
          else el.textContent = target.toLocaleString("fr-FR");
        }

        requestAnimationFrame(tick);
        observer.unobserve(el);
      });
    },
    { threshold: 0.5 }
  );

  counters.forEach((c) => observer.observe(c));
}

/* ===== Header sticky ===== */
function initStickyHeader() {
  const header = document.getElementById("siteHeader");
  if (!header) return;

  function onScroll() {
    header.classList.toggle("scrolled", window.scrollY > 60);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

/* ===== Défilement doux ===== */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="/#"], a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const href = link.getAttribute("href");
      const hashIndex = href.indexOf("#");
      if (hashIndex === -1) return;
      const target = document.querySelector(href.slice(hashIndex));
      if (!target) return;
      e.preventDefault();
      const headerHeight = document.getElementById("siteHeader")?.offsetHeight || 0;
      window.scrollTo({
        top: target.getBoundingClientRect().top + window.scrollY - headerHeight,
        behavior: "smooth",
      });
    });
  });
}

/* ===== Lightbox galerie ===== */
function initLightbox() {
  const lightbox = document.getElementById("lightbox");
  const lightboxImage = document.getElementById("lightboxImage");
  if (!lightbox || !lightboxImage) return;

  document.querySelectorAll("[data-lightbox]").forEach((img) => {
    img.addEventListener("click", () => {
      lightboxImage.src = img.src;
      lightboxImage.alt = img.alt;
      lightbox.classList.add("open");
      lightbox.setAttribute("aria-hidden", "false");
    });
  });

  function close() {
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
  }

  lightbox.querySelector(".lightbox-close").addEventListener("click", close);
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
}

/* ===== Retour en haut ===== */
function initBackToTop() {
  const button = document.getElementById("backToTop");
  if (!button) return;

  function onScroll() {
    button.classList.toggle("visible", window.scrollY > 400);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  button.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}
