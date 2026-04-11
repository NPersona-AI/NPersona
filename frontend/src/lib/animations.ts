import gsap from "gsap";

export const animations = {
  fadeIn: (selector: string | HTMLElement | null, delay: number = 0) => {
    if (!selector) return;
    gsap.fromTo(
      selector,
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 0.5, delay, ease: "power2.out" }
    );
  },
  
  pulse: (selector: string | HTMLElement | null) => {
    if (!selector) return;
    gsap.to(selector, {
      scale: 1.05,
      yoyo: true,
      repeat: -1,
      duration: 1.5,
      ease: "sine.inOut",
    });
  },

  graphNodeBirth: (selector: string | HTMLElement | null) => {
    if (!selector) return;
    gsap.fromTo(
      selector,
      { scale: 0, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.8, ease: "elastic.out(1, 0.5)" }
    );
  },
};
