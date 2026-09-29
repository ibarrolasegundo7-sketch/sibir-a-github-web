import html
import threading
import urllib.parse
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from html.parser import HTMLParser


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/153 Safari/537.36"
)

# Fuentes conocidas. Se consultan como búsquedas web, no se depende de una sola API.
SOURCE_QUERIES = [
    ("101 Soundboards", 'site:101soundboards.com/boards "{q}"'),
    ("101 Soundboards", 'site:101soundboards.com/sounds "{q}"'),
    ("Voicy", 'site:voicy.network "{q}" soundboard'),
    ("MyInstants", 'site:myinstants.com "{q}" sound'),
    ("MyInstants App", 'site:myinstants.app "{q}" soundboard'),
    ("Soundboard.com", 'site:soundboard.com "{q}" soundboard'),
    ("General", '"{q}" "voice lines" anime soundboard'),
    ("General", '"{q}" "voice clips" character'),
    ("General", '"{q}" "mp3" voice character'),
]

KNOWN_SOURCES = {
    "mayoi hachikuji": [
        (
            "101 Soundboards - Mayoi Hachikuji Voice",
            "https://www.101soundboards.com/boards/1621676-puella-magi-madoka-magica-side-story-magia-record-mobile-mayoi-hachikuji-voice",
        )
    ]
}


class SearchParser(HTMLParser):
    """Extrae resultados del HTML de DuckDuckGo."""

    def __init__(self):
        super().__init__()
        self.results = []
        self.in_result_link = False
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "")

        if tag == "a" and "result__a" in classes:
            self.in_result_link = True
            self.current = {
                "title": "",
                "url": attrs.get("href", ""),
            }

    def handle_data(self, data):
        if self.in_result_link and self.current is not None:
            self.current["title"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.in_result_link:
            self.in_result_link = False
            if self.current:
                self.current["title"] = " ".join(self.current["title"].split())
                self.results.append(self.current)
            self.current = None


def normalize_url(result_url):
    """Deshace redirecciones/codificación típicas de DuckDuckGo."""
    result_url = html.unescape(result_url or "").strip().replace("\\", "")

    for _ in range(5):
        parsed = urllib.parse.urlparse(result_url)
        params = urllib.parse.parse_qs(parsed.query)

        if params.get("uddg"):
            new_url = urllib.parse.unquote(params["uddg"][0])
        else:
            new_url = urllib.parse.unquote(result_url)

        if new_url == result_url:
            break
        result_url = new_url

    return result_url


def audio_related(title, url):
    """Evita resultados obviamente ajenos al audio."""
    text = f"{title} {url}".lower()
    words = (
        "sound", "audio", "voice", "voicebank", "voice line", "soundboard",
        "mp3", "clip", "quote", "quotes", "soundboard", "sounds"
    )
    return any(word in text for word in words)


def search_web(character, max_results=35):
    """Busca en varias fuentes y varias formas de consulta."""
    character = " ".join(character.split())
    if not character:
        return []

    # Variantes sencillas que ayudan con nombres escritos de forma ligeramente distinta.
    variants = [character]
    if "-" in character:
        variants.append(character.replace("-", " "))
    if "'" in character:
        variants.append(character.replace("'", ""))

    queries = []
    for variant in dict.fromkeys(variants):
        q = variant.replace('"', '')
        for source_name, template in SOURCE_QUERIES:
            queries.append((source_name, template.format(q=q)))

    found = []
    seen = set()

    for source_name, query in queries:
        search_url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        request = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                page = response.read().decode("utf-8", errors="replace")
        except Exception:
            continue

        parser = SearchParser()
        parser.feed(page)

        for result in parser.results:
            result_url = normalize_url(result["url"])
            title = result["title"].strip() or source_name

            if not result_url.startswith(("http://", "https://")):
                continue

            # Los resultados de búsquedas generales deben parecer relacionados con audio.
            if source_name == "General" and not audio_related(title, result_url):
                continue

            # Evita enlaces internos del propio buscador.
            blocked_hosts = (
                "duckduckgo.com",
                "duck.com",
            )
            host = (urllib.parse.urlparse(result_url).hostname or "").lower()
            if host in blocked_hosts:
                continue

            key = result_url.lower().rstrip("/")
            if key in seen:
                continue

            seen.add(key)
            found.append((f"[{source_name}] {title}", result_url))

            if len(found) >= max_results:
                return found

    return found


def unique_known_sources(character):
    key = " ".join(character.strip().lower().split())
    return KNOWN_SOURCES.get(key, [])


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de audio de personajes")
        self.root.geometry("900x650")
        self.root.minsize(780, 520)

        main = ttk.Frame(root, padding=18)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Personaje:").grid(row=0, column=0, sticky="w")

        self.character_var = tk.StringVar(value="Mayoi Hachikuji")
        self.entry = ttk.Entry(main, textvariable=self.character_var, width=52)
        self.entry.grid(row=0, column=1, sticky="ew", padx=8)
        self.entry.bind("<Return>", lambda _event: self.start_search())

        self.search_button = ttk.Button(main, text="Buscar audio", command=self.start_search)
        self.search_button.grid(row=0, column=2)

        ttk.Label(
            main,
            text=(
                "Busca en varias fuentes y muestra páginas donde puede haber clips, "
                "soundboards o frases de voz del personaje. Los enlaces se abren en el navegador."
            ),
            wraplength=820,
            justify="left",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(12, 15))

        self.status = ttk.Label(main, text="Listo")
        self.status.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))

        frame = ttk.Frame(main)
        frame.grid(row=3, column=0, columnspan=3, sticky="nsew")

        self.canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.results_frame = ttk.Frame(self.canvas)

        self.results_frame.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main.columnconfigure(1, weight=1)
        main.rowconfigure(3, weight=1)

        self.show_results(unique_known_sources(self.character_var.get()))

    def clear_results(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def open_url(self, url):
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError("La URL encontrada no es válida.")
            webbrowser.open_new_tab(url)
        except Exception as exc:
            messagebox.showerror("No se pudo abrir el enlace", str(exc))

    def copy_url(self, url):
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.root.update()
        self.status.configure(text="Enlace copiado al portapapeles.")

    def show_results(self, results):
        self.clear_results()

        if not results:
            ttk.Label(
                self.results_frame,
                text=(
                    "No encontré resultados. Probá el nombre completo del personaje "
                    "o agregá el nombre del anime al buscador."
                ),
                wraplength=700,
            ).pack(anchor="w", padx=5, pady=10)
            return

        for index, (title, url) in enumerate(results, start=1):
            card = ttk.Frame(self.results_frame, padding=10, relief="groove")
            card.pack(fill="x", padx=5, pady=5)

            left = ttk.Frame(card)
            left.pack(side="left", fill="x", expand=True)

            ttk.Label(
                left,
                text=f"{index}. {title}",
                font=("Segoe UI", 10, "bold"),
                wraplength=670,
                justify="left",
            ).pack(anchor="w")

            url_label = ttk.Label(
                left,
                text=url,
                foreground="#555",
                cursor="hand2",
                wraplength=670,
                justify="left",
            )
            url_label.pack(anchor="w", pady=(6, 0))
            url_label.bind("<Button-1>", lambda _e, u=url: self.open_url(u))

            actions = ttk.Frame(card)
            actions.pack(side="right", padx=(12, 0))

            ttk.Button(
                actions,
                text="Abrir",
                command=lambda u=url: self.open_url(u),
            ).pack(side="left")

            ttk.Button(
                actions,
                text="Copiar",
                command=lambda u=url: self.copy_url(u),
            ).pack(side="left", padx=(6, 0))

    def start_search(self):
        character = self.character_var.get().strip()
        if not character:
            messagebox.showwarning("Falta el personaje", "Escribí el nombre del personaje.")
            return

        self.search_button.configure(state="disabled")
        self.status.configure(text=f"Buscando audio de {character} en varias fuentes...")
        self.clear_results()

        threading.Thread(
            target=self.search_worker,
            args=(character,),
            daemon=True,
        ).start()

    def search_worker(self, character):
        results = unique_known_sources(character)
        web_results = search_web(character, max_results=35)

        existing = {url.rstrip("/").lower() for _, url in results}
        for item in web_results:
            if item[1].rstrip("/").lower() not in existing:
                results.append(item)
                existing.add(item[1].rstrip("/").lower())

        self.root.after(0, lambda: self.finish_search(results, character))

    def finish_search(self, results, character):
        self.show_results(results)
        self.status.configure(
            text=f"Encontrados {len(results)} resultados para {character}."
        )
        self.search_button.configure(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()
