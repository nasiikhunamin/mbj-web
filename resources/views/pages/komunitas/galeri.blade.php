@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Kegiatan Kami</h3>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item active text-secondary">Galeri</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- Gallery Start -->
<div class="container-fluid py-5" id="galeri">
    <div class="container">
        <div class="text-center mx-auto mb-5" style="max-width: 700px;">
            <h2 class="display-7 mb-4">Dokumentasi Kegiatan LPK Matahari Bulan Jepang Indonesia</h2>
        </div>

        <div class="row g-4">
            @forelse ($images as $image)
                @php
                    $filename = basename($image);
                    $number = (int) preg_replace('/\D+/', '', $filename);
                    $delays = ['0.1s', '0.3s', '0.5s'];
                @endphp
                <!-- Gallery Item {{ $number }} -->
                <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="{{ $delays[$loop->index % 3] }}">
                    <div class="card gallery-item h-100">
                        <img src="{{ asset('asset/img/'.$filename) }}"
                             class="card-img-top"
                             alt="Kegiatan {{ $number }}"
                             loading="lazy"
                             decoding="async">
                    </div>
                </div>
            @empty
                <div class="col-12 text-center text-body">
                    <p class="mb-0">Belum ada foto galeri.</p>
                </div>
            @endforelse
        </div>

        @if ($images->hasPages())
            @php
                $current = $images->currentPage();
                $last = $images->lastPage();
                $pages = [];

                // Tampilkan halaman pertama, terakhir, dan 1 halaman di kiri/kanan halaman aktif.
                for ($page = 1; $page <= $last; $page++) {
                    if ($page === 1 || $page === $last || abs($page - $current) <= 1) {
                        $pages[] = $page;
                    }
                }
            @endphp

            <nav class="gallery-pagination mt-5" aria-label="Navigasi halaman galeri">
                <ul class="pagination justify-content-center flex-wrap gap-2 mb-0">
                    <li class="page-item {{ $images->onFirstPage() ? 'disabled' : '' }}">
                        @if ($images->onFirstPage())
                            <span class="page-link" aria-hidden="true">&lsaquo;</span>
                        @else
                            <a class="page-link" href="{{ $images->previousPageUrl() }}" rel="prev" aria-label="Halaman sebelumnya">&lsaquo;</a>
                        @endif
                    </li>

                    @php $previous = 0; @endphp
                    @foreach ($pages as $page)
                        @if ($previous && $page - $previous > 1)
                            <li class="page-item disabled"><span class="page-link">&hellip;</span></li>
                        @endif

                        <li class="page-item {{ $page === $current ? 'active' : '' }}">
                            @if ($page === $current)
                                <span class="page-link" aria-current="page">{{ $page }}</span>
                            @else
                                <a class="page-link" href="{{ $images->url($page) }}">{{ $page }}</a>
                            @endif
                        </li>

                        @php $previous = $page; @endphp
                    @endforeach

                    <li class="page-item {{ $images->hasMorePages() ? '' : 'disabled' }}">
                        @if ($images->hasMorePages())
                            <a class="page-link" href="{{ $images->nextPageUrl() }}" rel="next" aria-label="Halaman berikutnya">&rsaquo;</a>
                        @else
                            <span class="page-link" aria-hidden="true">&rsaquo;</span>
                        @endif
                    </li>
                </ul>
            </nav>
        @endif
    </div>
</div>
<!-- Gallery End -->

<style>
.gallery-item {
    transition: transform 0.3s ease;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.gallery-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.gallery-item img {
    object-fit: cover;
    height: 250px;
}

.card-body {
    background: #fff;
}

/* Pagination galeri */
.gallery-pagination .pagination {
    margin-bottom: 0;
}

.gallery-pagination .page-link {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 46px;
    height: 46px;
    padding: 0 0.85rem;
    font-weight: 600;
    color: #002347;
    background: #fff;
    border: 1px solid #e5e9f0;
    border-radius: 10px;
    transition: all 0.2s ease;
}

.gallery-pagination .page-link:hover {
    color: #fff;
    background: #FB773C;
    border-color: #FB773C;
}

.gallery-pagination .page-link:focus {
    box-shadow: 0 0 0 0.2rem rgba(251, 119, 60, 0.25);
}

.gallery-pagination .page-item.active .page-link {
    color: #fff;
    background: #FB773C;
    border-color: #FB773C;
    box-shadow: 0 6px 12px rgba(251, 119, 60, 0.3);
}

.gallery-pagination .page-item.disabled .page-link {
    color: #b9c2cd;
    background: #f7f9fc;
    border-color: #eef1f6;
    box-shadow: none;
}

.gallery-pagination .page-item.disabled .page-link:hover {
    color: #b9c2cd;
    background: #f7f9fc;
    border-color: #eef1f6;
}
</style>

@endsection