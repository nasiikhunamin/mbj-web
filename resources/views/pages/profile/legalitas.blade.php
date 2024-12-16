@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Legalitas</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Legalitas</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h2 class="display-7">Izin Legalitas MBJ Indonesia</h2>
            <p class="lead text-muted">Klik pada gambar untuk memperbesar</p>
        </div>
    </div>
    <div class="row">
      @php
          $documents = [
              asset('asset/img/legality-1.jpeg'),
              asset('asset/img/legality-2.jpeg'),
          ];
      @endphp

        @foreach($documents as $index => $document)
        <div class="col-md-6 col-sm-6 mb-4">
            <div class="gallery-item">
                <a href="{{ $document }}" data-lightbox="legal-docs" data-title="Legal Document {{ $index + 1 }}">
                    <img src="{{ $document }}" alt="Legal Document {{ $index + 1 }}" class="img-fluid">
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

