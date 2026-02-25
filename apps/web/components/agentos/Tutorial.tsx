'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type Step = {
  id: string;
  title: { en: string; pt: string };
  content: { en: string; pt: string };
  selector?: string;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
};

const STEPS: Step[] = [
  {
    id: 'welcome',
    title: { en: 'Welcome to AgentOS', pt: 'Bem-vindo ao AgentOS' },
    content: {
      en: 'This is your autonomous agent orchestration environment. Let\'s show you how to deploy your first mission.',
      pt: 'Este é o seu ambiente de orquestração de agentes autônomos. Vamos mostrar como iniciar sua primeira missão.'
    },
    position: 'center'
  },
  {
    id: 'sidebar',
    title: { en: 'Neural Library', pt: 'Biblioteca Neural' },
    content: {
      en: 'Select an agent protocol from the sidebar to add it to your canvas.',
      pt: 'Selecione um protocolo de agente na barra lateral para adicioná-lo ao canvas.'
    },
    selector: 'aside:first-of-type',
    position: 'right'
  },
  {
    id: 'canvas',
    title: { en: 'Orchestration Canvas', pt: 'Canvas de Orquestração' },
    content: {
      en: 'Drag and connect agents here. Agents must be connected to the Supervisor to participate in the flow.',
      pt: 'Arraste e conecte os agentes aqui. Os agentes devem estar conectados ao Supervisor para participar do fluxo.'
    },
    selector: '.react-flow',
    position: 'center'
  },
  {
    id: 'config',
    title: { en: 'Node Parameters', pt: 'Parâmetros do Nó' },
    content: {
      en: 'Click on any agent to configure its designation, core engine, and directive prompt.',
      pt: 'Clique em qualquer agente para configurar sua designação, motor principal e prompt de diretiva.'
    },
    selector: 'aside:last-of-type',
    position: 'left'
  },
  {
    id: 'run',
    title: { en: 'Initialize Mission', pt: 'Iniciar Missão' },
    content: {
      en: 'When ready, click RUN MISSION to define your primary objective and deploy the agents.',
      pt: 'Quando estiver pronto, clique em RUN MISSION para definir seu objetivo primário e implantar os agentes.'
    },
    selector: 'button:contains("MISSION")',
    position: 'bottom'
  }
];

interface TutorialProps {
  language: 'en' | 'pt';
  onClose: () => void;
}

export default function Tutorial({ language, onClose }: TutorialProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const step = STEPS[currentStep];

  const next = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onClose();
    }
  };

  const prev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center pointer-events-none">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] pointer-events-auto" onClick={onClose} />

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="relative z-[210] w-full max-w-sm glass-panel-elevated p-6 pointer-events-auto"
      >
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-4 w-1 bg-cyber-cyan shadow-[0_0_8px_#00f3ff]" />
            <h3 className="text-sm font-black tracking-widest text-white uppercase italic">
              {step.title[language]}
            </h3>
          </div>
          <p className="text-xs font-mono text-neutral-300 leading-relaxed uppercase">
            {step.content[language]}
          </p>
        </div>

        <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/10">
          <span className="text-[10px] font-mono text-neutral-500">
            STEP_0{currentStep + 1} / 0{STEPS.length}
          </span>
          <div className="flex gap-2">
            {currentStep > 0 && (
              <button
                onClick={prev}
                className="text-[10px] font-bold text-neutral-500 hover:text-white uppercase transition-colors"
              >
                [ BACK ]
              </button>
            )}
            <button
              onClick={next}
              className="btn-cyber-primary !px-4 !py-1.5 !text-[10px]"
            >
              {currentStep === STEPS.length - 1 ? (language === 'en' ? 'FINISH' : 'CONCLUIR') : (language === 'en' ? 'NEXT_STEP' : 'PRÓXIMO')}
            </button>
          </div>
        </div>

        {/* Pointer element could be added here if we had coordinates */}
      </motion.div>
    </div>
  );
}
