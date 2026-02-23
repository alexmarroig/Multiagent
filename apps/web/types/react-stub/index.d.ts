declare namespace React {
  type ReactNode = any;
}

declare module 'react' {
  export = React;
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

export {};
