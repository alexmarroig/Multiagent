export const motionEase: [number, number, number, number] = [0.16, 1, 0.3, 1];

export const revealMotion = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.25 },
  transition: { duration: 0.6, ease: motionEase },
};
