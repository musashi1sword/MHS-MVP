import { useEffect, useState } from "react";

/**
 * Stand-in for the remote participant when no doctor video stream is attached.
 *
 * Tries a real photo first (drop a file at `frontend/public/doctor.jpg` to use
 * your own); falls back to a self-contained SVG portrait so the demo still looks
 * right with zero assets and no network.
 */
const DOCTOR_PHOTO = "/doctor.jpg";

export function DoctorAvatar({
  name = "Dr. Amina Okafor",
  title = "General Practitioner",
  simulated = false,
}: {
  name?: string;
  title?: string;
  simulated?: boolean;
}) {
  const [photoOk, setPhotoOk] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.onload = () => setPhotoOk(true);
    img.onerror = () => setPhotoOk(false);
    img.src = DOCTOR_PHOTO;
    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, []);

  return (
    <div className="doctor-avatar" aria-label={`${name}, ${title}`}>
      {photoOk ? (
        <img src={DOCTOR_PHOTO} alt={`${name}, ${title}`} />
      ) : (
        <svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" role="img" aria-hidden="true">
          <defs>
            <linearGradient id="da-bg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#1f6f8b" />
              <stop offset="1" stopColor="#12414f" />
            </linearGradient>
            <linearGradient id="da-coat" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#ffffff" />
              <stop offset="1" stopColor="#dfe7ec" />
            </linearGradient>
          </defs>
          <rect width="400" height="300" fill="url(#da-bg)" />
          <circle cx="200" cy="128" r="86" fill="#ffffff" opacity="0.06" />
          {/* shoulders / white coat */}
          <path d="M96 300c0-60 46-104 104-104s104 44 104 104Z" fill="url(#da-coat)" />
          <path d="M200 196l-24 104h48Z" fill="#eef2f5" />
          <path d="M188 198l12 34 12-34-12-10Z" fill="#5b7f8c" />
          {/* shirt + collar */}
          <path d="M176 196l24 22 24-22-6-14h-36Z" fill="#2f4858" />
          {/* stethoscope */}
          <path
            d="M182 190c-6 26-4 52 18 60M218 190c4 18 2 34-6 44"
            fill="none"
            stroke="#3a4a52"
            strokeWidth="5"
            strokeLinecap="round"
          />
          <circle cx="196" cy="256" r="9" fill="#3a4a52" />
          {/* neck + head */}
          <rect x="186" y="150" width="28" height="34" rx="12" fill="#c98a5e" />
          <path d="M160 122c0-30 18-52 40-52s40 22 40 52-18 54-40 54-40-24-40-54Z" fill="#db9c6f" />
          {/* hair */}
          <path d="M158 120c0-34 20-56 42-56s42 22 42 56c-8-12-18-18-42-18s-34 6-42 18Z" fill="#2b2b2b" />
          {/* eyes + mouth */}
          <circle cx="186" cy="120" r="3.4" fill="#2b2b2b" />
          <circle cx="214" cy="120" r="3.4" fill="#2b2b2b" />
          <path d="M192 140c5 5 11 5 16 0" fill="none" stroke="#8a5a3b" strokeWidth="3" strokeLinecap="round" />
        </svg>
      )}
      <span className="doctor-avatar__caption">
        <span className={`doctor-avatar__dot${simulated ? " is-sim" : ""}`} />
        {name} · {title}
        {simulated ? " · simulated" : ""}
      </span>
    </div>
  );
}
