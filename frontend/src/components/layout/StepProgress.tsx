"use client";

import { useAppStore } from "@/stores/appStore";

const STEPS = [
  { num: 1, label: "Upload" },
  { num: 2, label: "Graph Building" },
  { num: 3, label: "Explore Graph" },
  { num: 4, label: "Personas" },
  { num: 5, label: "Coverage" },
];

export default function StepProgress() {
  const currentStep = useAppStore((state) => state.currentStep);

  return (
    <div className="w-full glass shadow-none rounded-none border-t-0 border-l-0 border-r-0 px-6 py-4 fixed top-0 z-40 bg-background/80">
      <div className="max-w-4xl mx-auto flex items-center justify-between relative">
        {/* Background Line */}
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-white/10 rounded-full" />
        
        {/* Active Line */}
        <div 
          className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-gradient-to-r from-user to-adv rounded-full transition-all duration-700 ease-out"
          style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
        />

        {/* Steps */}
        {STEPS.map((step) => {
          const isActive = currentStep === step.num;
          const isPast = currentStep > step.num;

          return (
            <div key={step.num} className="relative z-10 flex flex-col items-center gap-2">
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-500
                  ${isActive ? "bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.8)] scale-110" : 
                    isPast ? "bg-gradient-to-br from-user to-user/50 text-white" : 
                    "bg-black border border-white/20 text-gray-500"}
                `}
              >
                {step.num}
              </div>
              <span className={`text-xs whitespace-nowrap hidden sm:block font-medium transition-colors duration-300
                ${isActive ? "text-white" : isPast ? "text-gray-300" : "text-gray-600"}`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
