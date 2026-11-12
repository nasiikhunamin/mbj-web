<?php

use Illuminate\Pagination\LengthAwarePaginator;
use Illuminate\Pagination\Paginator;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
|
| Here is where you can register web routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "web" middleware group. Make something great!
|
*/

Route::get('/', function () {
    return view('pages.home');
})->name('home');

// Profile Routes
Route::prefix('profile')->group(function () {
    Route::get('/tentang-perusahaan', function () {
        return view('pages.profile.tentang-perusahaan');
    })->name('profile.tentang-perusahaan');

    Route::get('/legalitas', function () {
        return view('pages.profile.legalitas');
    })->name('profile.legalitas');

    Route::get('/izin-so', function () {
        return view('pages.profile.izin-so');
    })->name('profile.izin-so');

    Route::get('/struktur-organisasi', function () {
        return view('pages.profile.struktur-organisasi');
    })->name('profile.struktur-organisasi');

    Route::get('/lokasi-pendidikan', function () {
        return view('pages.profile.lokasi-pendidikan');
    })->name('profile.lokasi-pendidikan');
});

// Informasi Routes
Route::prefix('informasi')->group(function () {
    Route::get('/pendaftaran', function () {
        return view('pages.informasi.pendaftaran');
    })->name('informasi.pendaftaran');

    Route::get('/prospek-karir', function () {
        return view('pages.informasi.prospek-karir');
    })->name('informasi.prospek-karir');

    Route::get('/silabus', function () {
        return view('pages.informasi.silabus');
    })->name('informasi.silabus');

    Route::get('/fasilitas', function () {
        return view('pages.informasi.fasilitas');
    })->name('informasi.fasilitas');

    Route::prefix('sertifikasi')->group(function () {
        Route::get('/', function () {
            return view('pages.informasi.sertifikasi');
        })->name('informasi.sertifikasi');
        Route::get('/coe', function () {
            return view('pages.informasi.sertifikasi.coe');
        })->name('informasi.sertifikasi.coe');
        Route::get('/jft', function () {
            return view('pages.informasi.sertifikasi.jft');
        })->name('informasi.sertifikasi.jft');
        Route::get('/jlpt', function () {
            return view('pages.informasi.sertifikasi.jlpt');
        })->name('informasi.sertifikasi.jlpt');
        Route::get('/ssw', function () {
            return view('pages.informasi.sertifikasi.ssw');
        })->name('informasi.sertifikasi.ssw');
    });

    Route::get('/perbedaan-magang-tokutei-ginou', function () {
        return view('pages.informasi.perbedaan-magang-tokutei-ginou');
    })->name('informasi.perbedaan-magang-tokutei-ginou');

    Route::get('/biaya-hidup-di-jepang', function () {
        return view('pages.informasi.biaya-hidup-di-jepang');
    })->name('informasi.biaya-hidup-di-jepang');
});

// Komunitas Routes
Route::prefix('komunitas')->group(function () {
    Route::get('/testimoni-alumni', function () {
        return view('pages.komunitas.testimoni');
    })->name('komunitas.testimoni-alumni');

    Route::get('/galeri', function () {
        $files = collect(glob(public_path('asset/img/galery-*')) ?: [])
            ->filter(fn ($path) => preg_match('/^galery-(\d+)\.(jpe?g|png|webp)$/i', basename($path)))
            ->sortBy(fn ($path) => (int) preg_replace('/\D+/', '', basename($path)))
            ->values();

        $perPage = 9;
        $currentPage = Paginator::resolveCurrentPage();

        $images = new LengthAwarePaginator(
            $files->forPage($currentPage, $perPage)->values(),
            $files->count(),
            $perPage,
            $currentPage,
            [
                'path' => route('komunitas.galeri'),
                'fragment' => 'galeri',
            ]
        );

        return view('pages.komunitas.galeri', compact('images'));
    })->name('komunitas.galeri');

    Route::get('/faq', function () {
        return view('pages.komunitas.faq');
    })->name('komunitas.faq');
});

// Daftar Sekarang Route
Route::get('/daftar', function () {
    return view('pages.informasi.pendaftaran');
})->name('daftar');
