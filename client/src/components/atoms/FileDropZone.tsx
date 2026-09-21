"use client";

import { Upload } from "lucide-react";
import { useRef, useState } from "react";

interface FileDropZoneProps {
  /** Hands over what was dropped or picked, one file at a time. */
  onFiles: (files: File[]) => void | Promise<void>;
  /** Whether a drop is under way: the zone says so rather than staying still. */
  busy?: boolean;
}

/**
 * Where a file is dropped, or picked from the disk.
 *
 * Both gestures reach the same place: dropping is what one does with a
 * capture already on screen, picking is what one does with a file one has to
 * go and find. Refusing either would send somebody through a detour.
 */
export function FileDropZone({ onFiles, busy = false }: FileDropZoneProps) {
  const input = useRef<HTMLInputElement>(null);
  const [isOver, setOver] = useState(false);

  function take(list: FileList | null) {
    const files = Array.from(list ?? []);
    if (files.length > 0) void onFiles(files);
  }

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(event) => {
        event.preventDefault();
        setOver(false);
        take(event.dataTransfer.files);
      }}
      className={`rounded-lg border border-dashed p-6 text-center transition-colors ${
        isOver ? "border-slate-500 bg-slate-100" : "border-slate-300 bg-white"
      }`}
    >
      <input
        ref={input}
        type="file"
        multiple
        hidden
        onChange={(event) => {
          take(event.target.files);
          // Emptied on purpose: dropping the same file twice in a row must
          // fire the change again, and it would not otherwise.
          event.target.value = "";
        }}
      />

      <Upload className="mx-auto size-5 text-slate-400" aria-hidden />
      <p className="mt-2 text-sm text-slate-600">
        Glissez un fichier ici, ou{" "}
        <button
          type="button"
          disabled={busy}
          onClick={() => input.current?.click()}
          className="cursor-pointer font-medium text-slate-900 underline underline-offset-2 disabled:cursor-default disabled:opacity-50"
        >
          parcourez votre disque
        </button>
        .
      </p>
      <p className="mt-1 text-xs text-slate-400">
        {busy ? "Téléversement en cours…" : "10 Mo par fichier au maximum."}
      </p>
    </div>
  );
}
