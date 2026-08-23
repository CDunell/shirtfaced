export const PICTURE_SCENES = [
  { id: "curb", name: "Crooked Curb", colour: "#ffc93c" },
  { id: "puddle", name: "Long Puddle", colour: "#3ec6e0" },
  { id: "crumb", name: "Crumb Hill", colour: "#ff8c42" },
  { id: "drain", name: "Moonlight Drain", colour: "#c7b8ff" },
  { id: "bin", name: "Under-the-Bin", colour: "#7ed957" },
] as const;

export type PictureSceneId = (typeof PICTURE_SCENES)[number]["id"];

type SceneProps = { scene: PictureSceneId };

const line = {
  fill: "none",
  stroke: "#1c1a17",
  strokeWidth: 3,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function CurbScene() {
  return (
    <>
      <rect width="800" height="500" fill="#fffaf0" />
      <circle cx="670" cy="78" r="42" fill="#ff6f9c" stroke="#1c1a17" strokeWidth="3" />
      <path d="M0 326 H800 V500 H0Z" fill="#f1e9d8" />
      <path d="M0 326 H800 M0 405 H800 M118 326l-20 79m180-79 18 79m205-79-12 79m202-79 20 79" {...line} />
      <path d="M0 405 H800 V500 H0Z" fill="#3ec6e0" fillOpacity=".28" />
      <path d="M75 326v-92h142v92M75 234h142M105 234l41-47 41 47M104 271h35v55m37-54h21" {...line} />
      <path d="M548 326v-72h120v72m-120-72 60-45 60 45m-95 31h30v41m34-40h24" {...line} />
      <path d="M294 326v-67h98v67m-81-67v-27h64v27m-47 29h37" {...line} />
      <path d="M450 326v-85m-34 0h68m-56-29h44v29m-32 36h22" {...line} />
      <text x="450" y="229" textAnchor="middle" fontSize="14" fontWeight="900" fill="#1c1a17">THE CURB</text>
      <path d="M24 131c23-27 49-22 62-3 27-15 51 2 51 21H25c-9-5-9-12-1-18Zm249-54c17-20 36-16 46-2 19-10 38 1 38 16h-82c-7-4-7-9-2-14Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
      <path d="M704 326v-61m0 19c-25-2-34-22-27-38 22 2 30 18 27 38Zm1-12c24-2 35-20 30-37-22 0-31 17-30 37Z" {...line} />
      <path d="M25 433l34-12 29 10 38-14 40 13m244 22 35-16 29 13 31-9" {...line} />
    </>
  );
}

function PuddleScene() {
  return (
    <>
      <rect width="800" height="500" fill="#addff0" />
      <circle cx="112" cy="82" r="43" fill="#ffc93c" stroke="#1c1a17" strokeWidth="3" />
      <path d="M0 285c115-48 216-4 322-25 114-22 208-73 478-16V500H0Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
      <path d="M20 389c69-64 156-79 226-36 62 38 120 38 189-4 83-51 225-30 339 58-99 76-226 89-363 61-139-29-256 8-391-79Z" fill="#3ec6e0" fillOpacity=".75" stroke="#1c1a17" strokeWidth="3" />
      <path d="M89 399c51-31 93-34 144-10m287 23c51-28 102-22 152 7m-316 3c33-18 66-17 99 0" {...line} />
      <path d="M614 344l20-77m-3 23 27-25m-31 42-27-31m85 79 8-55m-6 20 23-16m-20 32-22-19" {...line} />
      <path d="M188 301v-78h122v78m-122-78 61-50 61 50m-89 23h28v55m25-54h18" {...line} />
      <path d="M422 276c15-34 43-41 60-26 22-31 58-13 58 19-34-10-72-7-118 7Z" fill="#7ed957" stroke="#1c1a17" strokeWidth="3" />
      <path d="M43 149c22-26 47-21 60-3 26-14 49 2 49 20H44c-9-5-9-12-1-17Zm461-63c18-21 38-17 48-3 21-11 40 2 40 17h-86c-7-4-7-9-2-14Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
      <path d="M344 315l15-20 19 20m-11-13v-38m-16 0h32" {...line} />
      <text x="367" y="254" textAnchor="middle" fontSize="13" fontWeight="900" fill="#1c1a17">LONG PUDDLE</text>
    </>
  );
}

function CrumbScene() {
  return (
    <>
      <rect width="800" height="500" fill="#ffd65a" />
      <path d="M0 382c96-27 169-24 239-5 100 27 194 23 288-5 92-28 181-24 273 5v123H0Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
      <path d="M145 393 350 158l206 235Z" fill="#ff8c42" stroke="#1c1a17" strokeWidth="3" />
      <path d="m306 207 44-49 48 55-31-5-18 26-17-29Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
      <path d="M231 293l26-14m169 22 31-13m-102 55 25-10m-112 24 20-9" {...line} />
      <path d="M78 382v-87h96v87m-96-87 48-42 48 42m-67 24h24v63" {...line} />
      <path d="M625 382v-89m-35 0h70m-57-30h44v30" {...line} />
      <text x="625" y="282" textAnchor="middle" fontSize="13" fontWeight="900" fill="#1c1a17">CRUMB HILL</text>
      <path d="M603 382c3-37 25-56 48-48 5-25 34-31 48-9 22-8 43 12 38 37-42-5-86 2-134 20Z" fill="#7ed957" stroke="#1c1a17" strokeWidth="3" />
      <path d="M61 113c20-24 43-19 55-3 24-13 45 2 45 19H62c-8-5-8-11-1-16Zm492 11c21-25 45-20 57-3 25-14 48 2 48 19H554c-8-5-8-11-1-16Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
      <path d="m43 431 14-8 11 10 18-6 12 10m473-2 17-10 13 11 21-7 13 9" {...line} />
    </>
  );
}

function DrainScene() {
  return (
    <>
      <rect width="800" height="500" fill="#29253d" />
      <circle cx="655" cy="91" r="49" fill="#fffaf0" stroke="#c7b8ff" strokeWidth="4" />
      <circle cx="635" cy="78" r="8" fill="#c7b8ff" />
      <circle cx="674" cy="109" r="6" fill="#c7b8ff" />
      <path d="M0 295H800V500H0Z" fill="#c7b8ff" />
      <path d="M0 295H800M0 408H800M91 295l-20 113m190-113 18 113m220-113-14 113m210-113 21 113" {...line} />
      <path d="M258 408v-91h284v91m-258 0v-64h232v64" fill="#1c1a17" stroke="#1c1a17" strokeWidth="3" />
      <path d="M302 349v54m32-54v54m32-54v54m32-54v54m32-54v54m32-54v54m32-54v54" stroke="#fffaf0" strokeWidth="5" strokeLinecap="round" />
      <path d="M54 246h147m-119 0v-73h92v73m-92-73 46-41 46 41" stroke="#fffaf0" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M588 295v-76m-35 0h70m-57-29h44v29" stroke="#fffaf0" strokeWidth="3" fill="none" strokeLinecap="round" />
      <text x="588" y="209" textAnchor="middle" fontSize="13" fontWeight="900" fill="#fffaf0">MOONLIGHT DRAIN</text>
      <path d="M70 74h8m35 43h8m174-45h8m50 58h8m190-67h8m152 88h8" stroke="#fffaf0" strokeWidth="5" strokeLinecap="round" />
      <path d="M40 454c66-27 131-27 197 0m328-4c60-24 119-23 178 3" stroke="#1c1a17" strokeWidth="3" fill="none" strokeLinecap="round" />
    </>
  );
}

function BinScene() {
  return (
    <>
      <rect width="800" height="500" fill="#c8ef63" />
      <path d="M0 357H800V500H0Z" fill="#f1e9d8" stroke="#1c1a17" strokeWidth="3" />
      <path d="M213 116h346l-28 267H244Z" fill="#3ec6e0" stroke="#1c1a17" strokeWidth="4" />
      <path d="M187 116h397v-35H187Z" fill="#1c1a17" />
      <path d="M247 82V57h278v25" {...line} />
      <path d="M291 151l-18 175m94-175-7 175m105-175 15 175" stroke="#1c1a17" strokeWidth="3" strokeLinecap="round" />
      <circle cx="269" cy="393" r="25" fill="#1c1a17" />
      <circle cx="511" cy="393" r="25" fill="#1c1a17" />
      <path d="M121 357v-76m-33 0h66m-53-27h40v27" {...line} />
      <text x="121" y="272" textAnchor="middle" fontSize="12" fontWeight="900" fill="#1c1a17">WEIRDOS BELOW</text>
      <path d="M35 356c2-43 28-64 54-54 7-27 39-33 54-8 25-8 48 15 41 43-48-7-98 0-149 19Zm574 0c3-37 25-56 48-48 5-25 34-31 48-9 22-8 43 12 38 37-42-5-86 2-134 20Z" fill="#7ed957" stroke="#1c1a17" strokeWidth="3" />
      <path d="M77 429h98m425 0h120m-388 14h118" {...line} />
      <path d="m88 455 17-12 19 12 24-10m461 10 15-12 20 12 25-10" {...line} />
      <path d="M58 105c20-24 43-19 55-3 24-13 45 2 45 19H59c-8-5-8-11-1-16Zm547 20c21-25 45-20 57-3 25-14 48 2 48 19H606c-8-5-8-11-1-16Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
    </>
  );
}

export function PictureScene({ scene }: SceneProps) {
  return (
    <svg viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full" aria-hidden="true">
      {scene === "curb" && <CurbScene />}
      {scene === "puddle" && <PuddleScene />}
      {scene === "crumb" && <CrumbScene />}
      {scene === "drain" && <DrainScene />}
      {scene === "bin" && <BinScene />}
    </svg>
  );
}
