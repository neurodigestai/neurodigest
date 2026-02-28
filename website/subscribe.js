/* ================================================================
   Neuro-AI Research Digest — Interactive Scripts
   ================================================================
   • Neural network canvas animation
   • Scroll-triggered animations
   • Counter animation for stats
   • Google Form subscription handler
   ================================================================ */

(function () {
    "use strict";

    // ────────────────────────────────────────────────────────────────
    // CONFIG — Update these after creating your Google Form
    // ────────────────────────────────────────────────────────────────

    // HOW TO GET THESE VALUES:
    // 1. Create a Google Form with one "Email" question
    // 2. Click the ⋮ menu → "Get pre-filled link"
    // 3. Fill in a test email, click "Get link"
    // 4. The URL will look like:
    //    https://docs.google.com/forms/d/e/FORM_ID/viewform?usp=pp_url&entry.ENTRY_ID=test@email.com
    // 5. Copy FORM_ID and ENTRY_ID below

    const GOOGLE_FORM_ACTION =
        "https://docs.google.com/forms/d/e/YOUR_FORM_ID/formResponse";
    const GOOGLE_FORM_ENTRY = "entry.YOUR_ENTRY_ID";

    // ────────────────────────────────────────────────────────────────
    // 1. NEURAL NETWORK CANVAS
    // ────────────────────────────────────────────────────────────────

    const canvas = document.getElementById("neural-canvas");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        let nodes = [];
        let animFrame;
        const NODE_COUNT = 60;
        const CONNECTION_DISTANCE = 150;

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        function createNodes() {
            nodes = [];
            for (let i = 0; i < NODE_COUNT; i++) {
                nodes.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.4,
                    vy: (Math.random() - 0.5) * 0.4,
                    r: Math.random() * 2 + 1,
                    pulse: Math.random() * Math.PI * 2,
                });
            }
        }

        function drawNetwork() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw connections
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[i].x - nodes[j].x;
                    const dy = nodes[i].y - nodes[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < CONNECTION_DISTANCE) {
                        const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.15;
                        ctx.strokeStyle = `rgba(108, 92, 231, ${alpha})`;
                        ctx.lineWidth = 0.5;
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.stroke();
                    }
                }
            }

            // Draw nodes
            for (const node of nodes) {
                node.pulse += 0.02;
                const glow = 0.4 + Math.sin(node.pulse) * 0.3;

                ctx.fillStyle = `rgba(162, 155, 254, ${glow})`;
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
                ctx.fill();

                // Move
                node.x += node.vx;
                node.y += node.vy;

                // Bounce
                if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
                if (node.y < 0 || node.y > canvas.height) node.vy *= -1;
            }

            animFrame = requestAnimationFrame(drawNetwork);
        }

        resize();
        createNodes();
        drawNetwork();

        let resizeTimeout;
        window.addEventListener("resize", () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                resize();
                createNodes();
            }, 200);
        });
    }

    // ────────────────────────────────────────────────────────────────
    // 2. SCROLL ANIMATIONS
    // ────────────────────────────────────────────────────────────────

    // Nav scroll effect
    const nav = document.getElementById("nav");
    window.addEventListener("scroll", () => {
        if (window.scrollY > 50) {
            nav.classList.add("scrolled");
        } else {
            nav.classList.remove("scrolled");
        }
    });

    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.15,
        rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                const delay = parseInt(entry.target.dataset.delay || "0", 10);
                setTimeout(() => {
                    entry.target.classList.add("visible");
                }, delay);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe feature cards
    document.querySelectorAll(".feature-card").forEach((card) => {
        observer.observe(card);
    });

    // Observe pipeline steps
    document.querySelectorAll(".pipeline-step").forEach((step, i) => {
        step.dataset.delay = String(i * 150);
        observer.observe(step);
    });

    // ────────────────────────────────────────────────────────────────
    // 3. COUNTER ANIMATION
    // ────────────────────────────────────────────────────────────────

    const counterObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    animateCounters();
                    counterObserver.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.5 }
    );

    const statsSection = document.querySelector(".hero-stats");
    if (statsSection) {
        counterObserver.observe(statsSection);
    }

    function animateCounters() {
        document.querySelectorAll(".stat-number").forEach((el) => {
            const target = parseInt(el.dataset.count, 10);
            const duration = 1500;
            const start = performance.now();

            function update(now) {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(target * eased);

                if (progress < 1) {
                    requestAnimationFrame(update);
                } else {
                    el.textContent = target;
                }
            }

            requestAnimationFrame(update);
        });
    }

    // ────────────────────────────────────────────────────────────────
    // 4. SUBSCRIPTION FORM (Google Form POST)
    // ────────────────────────────────────────────────────────────────

    const form = document.getElementById("subscribe-form");
    const emailInput = document.getElementById("email");
    const btn = document.getElementById("subscribeBtn");
    const msgEl = document.getElementById("form-message");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const email = emailInput.value.trim();
            if (!email) return;

            // Basic email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showMessage("Please enter a valid email address.", "error");
                return;
            }

            // Loading state
            btn.classList.add("loading");
            btn.disabled = true;
            msgEl.textContent = "";
            msgEl.className = "form-message";

            try {
                // Build form data for Google Forms
                const formData = new URLSearchParams();
                formData.append(GOOGLE_FORM_ENTRY, email);

                // Google Forms doesn't support CORS, so we use no-cors mode.
                // The response will be opaque, but the submission still goes through.
                await fetch(GOOGLE_FORM_ACTION, {
                    method: "POST",
                    mode: "no-cors",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: formData.toString(),
                });

                // No-cors means we can't read the response, but if fetch didn't
                // throw, the request was sent successfully.
                btn.classList.remove("loading");
                btn.classList.add("success");
                showMessage(
                    "Subscription successful! You'll receive the next digest. 🎉",
                    "success"
                );
                emailInput.value = "";

                // Reset button after 4 seconds
                setTimeout(() => {
                    btn.classList.remove("success");
                    btn.disabled = false;
                }, 4000);
            } catch (err) {
                btn.classList.remove("loading");
                btn.disabled = false;
                showMessage(
                    "Something went wrong. Please try again or email us directly.",
                    "error"
                );
                console.error("Subscription error:", err);
            }
        });
    }

    function showMessage(text, type) {
        msgEl.textContent = text;
        msgEl.className = `form-message ${type}`;
    }

    // ────────────────────────────────────────────────────────────────
    // 5. SMOOTH SCROLL for anchor links
    // ────────────────────────────────────────────────────────────────

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute("href"));
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
})();
