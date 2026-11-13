@extends('layouts.master')

@section('page-style')
<style>
    .akreditasi-gallery .gallery-item {
        display: flex;
        align-items: center;
        justify-content: center;
        height: clamp(300px, 45vw, 560px);
        padding: 12px;
        background: #fff;
        border: 1px solid #eee;
        border-radius: .5rem;
        box-shadow: 0 .125rem .5rem rgba(0, 0, 0, .06);
        transition: box-shadow .2s ease;
    }
    .akreditasi-gallery .gallery-item:hover {
        box-shadow: 0 .5rem 1rem rgba(0, 0, 0, .12);
    }
    .akreditasi-gallery .gallery-item > a {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
    }
    .akreditasi-gallery .gallery-item img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }
</style>
@endsection

@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Akreditasi</h3>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="{{ route('home') }}" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Akreditasi</li>
        </ol>
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery akreditasi-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h2 class="display-7">Akreditasi MBJ Indonesia</h2>
            <p class="lead text-muted">Klik pada gambar untuk memperbesar</p>
        </div>
    </div>
    <div class="row">
      @php
          $documents = [
              asset('asset/img/akreditasi-1.jpeg'),
              asset('asset/img/akreditasi-2.jpeg'),
              asset('asset/img/akreditasi-3.jpeg'),
              asset('asset/img/akreditasi-4.jpeg'),
          ];
      @endphp

        @foreach($documents as $index => $document)
        <div class="col-md-6 col-sm-6 mb-4">
            <div class="gallery-item">
                <a href="{{ $document }}" data-lightbox="legal-docs" data-title="Akreditasi {{ $index + 1 }}">
                    <img src="{{ $document }}" alt="Akreditasi {{ $index + 1 }}" class="img-fluid">
                </a>
            </div>
        </div>
        @endforeach
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/lightbox2/2.11.3/js/lightbox.min.js"></script>

<!-- About End -->

@endsection
