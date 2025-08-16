import streamlit as st
import joblib
import requests

# ==== Load Data ====
df = joblib.load('movie_df.pkl')
model = joblib.load('movie_model.pkl')
vectors = joblib.load('movie_vectors.pkl')

# ==== Page Config ====
st.set_page_config(page_title="Movie Recommendation App", layout="wide")

# ==== Page State ====
if "page" not in st.session_state:
    st.session_state.page = "select"
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

# ==== Theme ====
theme = st.sidebar.radio("Choose Theme", ["🌞 Light", "🌚 Dark"])
if theme == "🌚 Dark":
    st.markdown("""
        <style>
            body { background-color: #0e1117; color: white; }
        </style>
    """, unsafe_allow_html=True)

# ==== CSS for Clickable Posters ====
st.markdown("""
    <style>
        .poster-btn {
            background: none;
            border: none;
            padding: 0;
            cursor: pointer;
        }
        .poster-btn img {
            border-radius: 8px;
            transition: transform 0.2s ease-in-out;
        }
        .poster-btn img:hover {
            transform: scale(1.05);
        }
        .poster-title {
            text-align: center;
            font-weight: bold;
            margin-top: 5px;
            color: #ff4b4b;
        }
    </style>
""", unsafe_allow_html=True)

# ==== Sidebar ====
with st.sidebar:
    st.title("📞 Contact Us")
    st.image("D:\Project\imakhilesh_mathyal_qr.png", width=150)
    st.text_input("📨 Email", placeholder="Enter your email")
    st.text_input("📞 Phone", placeholder="Enter your phone number")
    st.text_area("📬 Message", placeholder="Enter your message here")
    st.markdown("TO Refresh Page: <a href='http://192.168.31.244:8501/' target='_blank'>CLICK HERE</a>", unsafe_allow_html=True)
    st.title("Built by - Akhilesh Mathyal")

# ==== Cache Poster Fetch ====
@st.cache_data
def get_poster_url(movie_id):
    resp = requests.get(f"http://www.omdbapi.com/?i={movie_id}&apikey=36279439")
    poster_url = resp.json().get('Poster', "")
    if not poster_url or poster_url == "N/A":
        poster_url = "https://via.placeholder.com/400x600?text=No+Image"
    return poster_url

# ==== Fetch Movie Details for Hover Card ====
@st.cache_data
def get_movie_details(movie_id):
    """Fetch extra movie details including trailer search link."""
    resp = requests.get(f"http://www.omdbapi.com/?i={movie_id}&apikey=36279439")
    data = resp.json()
    title = data.get("Title", "Unknown")
    year = data.get("Year", "")
    rating = data.get("imdbRating", "N/A")
    plot = data.get("Plot", "No plot available.")
    trailer_link = f"https://www.youtube.com/results?search_query={title}+trailer"
    return {
        "title": title,
        "year": year,
        "rating": rating,
        "plot": plot,
        "trailer_link": trailer_link
    }

# ==== Function to Display Posters with Hover Info ====
def display_posters(movie_iterable):
    cols = st.columns(5)  # 5 posters per row

    st.markdown("""
        <style>
            .poster-container {
                position: relative;
                display: inline-block;
            }
            .hover-info {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                background: rgba(0, 0, 0, 0.85);
                color: white;
                padding: 10px;
                font-size: 12px;
                opacity: 0;
                transition: opacity 0.3s ease-in-out;
                border-radius: 0 0 8px 8px;
                max-height: 200px;
                overflow-y: auto;
            }
            .poster-container:hover .hover-info {
                opacity: 1;
            }
            .hover-title {
                font-weight: bold;
                color: #ff4b4b;
            }
            .hover-rating {
                color: gold;
            }
            .hover-trailer a {
                color: #00adee;
                text-decoration: underline;
            }
        </style>
    """, unsafe_allow_html=True)

    for idx, movie in enumerate(movie_iterable):
        with cols[idx % 5]:
            poster_url = get_poster_url(movie.movie_id)
            details = get_movie_details(movie.movie_id)
            st.markdown(
                f"""
                <div class="poster-container">
                    <form action="" method="get" style="margin:0;">
                        <button class="poster-btn" type="submit" name="selected" value="{movie.name}">
                            <img src="{poster_url}" width="400">
                        </button>
                    </form>
                    <div class="hover-info">
                        <div class="hover-title">{details['title']} ({details['year']})</div>
                        <div class="hover-rating">⭐ {details['rating']}</div>
                        <div class="hover-plot">{details['plot']}</div>
                        <div class="hover-trailer"><a href="{details['trailer_link']}" target="_blank">▶ Watch Trailer</a></div>
                    </div>
                </div>
                <div class="poster-title">{movie.name}</div>
                """,
                unsafe_allow_html=True
            )

# ==== Function to Show Recommendations ====
def show_recommendations(movie_name):
    matches = df[df["name"].str.casefold() == str(movie_name).casefold()]
    if matches.empty:
        st.error(f"Movie not found: {movie_name}")
        return

    movie_index = matches.index[0]
    movie_vector = vectors[movie_index]
    distances, indexes = model.kneighbors([movie_vector], n_neighbors=10)  # 10 posters

    recommended_df = df.loc[indexes[0][1:], ["name", "movie_id"]]
    recommended_iter = recommended_df.itertuples(index=False)

    main_poster = get_poster_url(df.loc[movie_index].movie_id)
    st.markdown(f"<h1 style='text-align:center; color:#ff4b4b;'>{movie_name}</h1>", unsafe_allow_html=True)
    st.image(main_poster, width=500, caption=movie_name, use_container_width=False)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(f"<h2 style='color:#ff4b4b;'>Recommended Movies</h2>", unsafe_allow_html=True)
    display_posters(recommended_iter)

# ==== Handle Poster Click ====
query_params = st.query_params
if "selected" in query_params:
    sel = query_params["selected"]
    if isinstance(sel, list):
        sel = sel[0] if sel else None
    if sel:
        st.session_state.selected_movie = sel
        st.session_state.page = "recommend"

# ==== Search Bar ====
if st.session_state.page == "select":
    search_term = st.text_input("🔍 Search for a movie", "").strip()
    if search_term:
        filtered_df = df[df.name.str.contains(search_term, case=False, na=False)]
    else:
        filtered_df = df
else:
    filtered_df = df

# ==== PAGE 1 – All Movies ====
if st.session_state.page == "select":
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>Select a Movie</h1>", unsafe_allow_html=True)
    display_posters(filtered_df[["name", "movie_id"]].itertuples(index=False))

# ==== PAGE 2 – Recommendations ====
elif st.session_state.page == "recommend":
    if st.session_state.selected_movie:
        show_recommendations(st.session_state.selected_movie)
    else:
        st.warning("No movie selected. Please choose a movie first.")
    if st.button("⬅ Back"):
        st.session_state.page = "select"
