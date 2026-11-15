import * as Dialog from "@radix-ui/react-dialog";
import { Info } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "./ui";

const KEY = "hg.notice.v1";

/**
 * Shown once, on first entering an account that holds sample data (Constitution V):
 * what the data is, what HappyGut is, and that it isn't for medical decisions.
 * It can only be closed by acknowledging it.
 */
export function DataNotice() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(() => localStorage.getItem(KEY) !== "1");
  const accept = (): void => {
    localStorage.setItem(KEY, "1");
    setOpen(false);
  };
  return (
    <Dialog.Root open={open}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-ink/55 backdrop-blur-sm" />
        <Dialog.Content
          aria-describedby="notice-body"
          onEscapeKeyDown={(e) => e.preventDefault()}
          onPointerDownOutside={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
          className="fixed inset-x-4 top-1/2 z-[70] mx-auto max-w-md -translate-y-1/2 animate-pop rounded-[28px] bg-card p-6 shadow-2xl"
        >
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-soft text-brand-deep">
            <Info className="h-6 w-6" />
          </span>
          <Dialog.Title className="mt-4 text-2xl font-bold">{t("notice.title")}</Dialog.Title>
          <div id="notice-body" className="mt-3 space-y-3 text-[15px] text-ink-soft">
            <p>{t("notice.data")}</p>
            <p>{t("notice.purpose")}</p>
            <p className="font-semibold text-ink">{t("notice.medical")}</p>
          </div>
          <Button size="lg" className="mt-6 w-full" onClick={accept}>
            {t("notice.accept")}
          </Button>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
