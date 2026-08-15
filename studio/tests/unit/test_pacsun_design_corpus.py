from pathlib import Path

from app.services.design_corpus.collector import provenance_record, sha256_bytes
from app.services.design_corpus.pacsun import Product, canonical_url, discover, is_graphic_candidate, parse_category, parse_product, select_images, select_sample
FIXTURES = Path(__file__).parents[1] / "fixtures" / "pacsun"

def test_category_parsing_and_detected_pagination():
    products, next_url = parse_category((FIXTURES / "category.html").read_text(), "https://www.pacsun.com/mens/graphic-tees/")
    assert len(products) == 3
    assert next_url == "https://www.pacsun.com/mens/graphic-tees/?start=12"

def test_noise_filtering():
    assert is_graphic_candidate(Product("Metallica Skull Tour T-Shirt", "https://www.pacsun.com/a.html"))
    assert not is_graphic_candidate(Product("3 Pack Cut Off Muscle T-Shirts", "https://www.pacsun.com/b.html"))
    assert not is_graphic_candidate(Product("Cyber Long Sleeve Soccer Jersey", "https://www.pacsun.com/c.html"))

def test_canonical_url_drops_query_and_fragment():
    assert canonical_url("/foo/bar.html?dwvar_x=1#top") == "https://www.pacsun.com/foo/bar.html"

def test_product_parsing_and_images():
    product = parse_product((FIXTURES / "product.html").read_text(), "https://www.pacsun.com/x.html")
    assert product.name == "Metallica Skull Tour T-Shirt"; assert product.brand == "Metallica"; assert product.price == "USD 40.00"; assert "front.jpg" in product.image_urls[0]; assert len(select_images(product.image_urls)) == 3

def test_sha256_provenance():
    data=b"real image bytes"; row=provenance_record(source_id="pacsun/example",image_stem="image-01",source_url="https://img",data=data)
    assert row["content_hash"] == sha256_bytes(data); assert row["byte_size"] == len(data); assert row["provenance_id"] == "pacsun/example/image-01"

def test_duplicate_catalogue_urls_are_collapsed_and_dry_discovery_has_no_writes(tmp_path):
    first=(FIXTURES/"category.html").read_bytes(); second=b"<html></html>"; calls=[]
    def fake_fetch(url): calls.append(url); return (first if len(calls)==1 else second),"text/html"
    products,failures=discover(fetch=fake_fetch); assert not failures; assert len({p.source_url for p in products})==len(products); assert list(tmp_path.iterdir())==[]

def test_sample_is_not_first_n_only():
    products=[Product(f"Plain Graphic Tee {i}",f"https://www.pacsun.com/p{i}.html") for i in range(30)]; products[20]=Product("Metallica Tour T-Shirt","https://www.pacsun.com/music.html"); selected=select_sample(products,12)
    assert any(p.source_url.endswith("music.html") for p in selected); assert selected != products[:12]

def test_image_duplicate_input_urls_are_removed():
    assert select_images(["https://x/front.jpg","https://x/front.jpg","https://x/back.jpg"]) == ["https://x/front.jpg","https://x/back.jpg"]
