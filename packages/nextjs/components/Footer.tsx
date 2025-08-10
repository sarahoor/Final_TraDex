import React from "react";
import { CurrencyDollarIcon, HeartIcon } from "@heroicons/react/24/outline";
import { BuidlGuidlLogo } from "~~/components/assets/BuidlGuidlLogo";
import { useGlobalState } from "~~/services/store/store";

/**
 * Clean footer for DeFi Aggregator
 */
export const Footer = () => {
  const nativeCurrencyPrice = useGlobalState(state => state.nativeCurrency.price);

  return (
    <footer className="w-full py-5 px-4 border-t border-base-300 mt-16 text-sm text-base-content/70">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-2">
          <a href="https://t.me/joinchat/KByvmRe5wkR-8F_zz6AjpA" target="_blank" rel="noreferrer" className="link">
            Support
          </a>
        </div>

        <div className="flex items-center gap-2">
          <p className="m-0 flex items-center gap-1">
            Built with <HeartIcon className="inline-block h-4 w-4" /> at
            <a
              className="flex items-center gap-1 link"
              href="https://buidlguidl.com/"
              target="_blank"
              rel="noreferrer"
            >
              <BuidlGuidlLogo className="w-4 h-4" />
              BuidlGuidl
            </a>
          </p>
          <span>·</span>
        </div>
      </div>
    </footer>
  );
};
