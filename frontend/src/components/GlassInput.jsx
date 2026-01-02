import React from 'react';

const GlassInput = ({
  className = "",
  error = false,
  ...props
}) => {
  const baseClasses = "backdrop-blur-sm bg-white/5 border rounded-lg px-4 py-3 text-white placeholder-white/60 transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent";

  const normalClasses = "border-white/20 focus:bg-white/10 focus:border-white/40 focus:ring-white/30";
  const errorClasses = "border-red-400/30 focus:border-red-400/50 focus:ring-red-400/30";

  return (
    <input
      className={`${baseClasses} ${error ? errorClasses : normalClasses} ${className}`}
      {...props}
    />
  );
};

export default GlassInput;


