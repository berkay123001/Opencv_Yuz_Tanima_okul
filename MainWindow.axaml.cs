using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Media.Imaging;
using Avalonia.Platform.Storage;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace ObjectDetection;

public partial class MainWindow : Avalonia.Controls.Window
{
    private string? currentImagePath;
    private readonly string cascadePath = "haarcascade_frontalface_default.xml";
    private readonly string pythonScript = "face_detector.py";
    private readonly string cameraScript = "camera_face_detector.py";
    private readonly string advancedScript = "advanced_face_recognition.py";
    private List<string> knownPeople = new List<string>();

    public MainWindow()
    {
        InitializeComponent();
        
        var loadButton = this.FindControl<Button>("LoadImageButton");
        var detectButton = this.FindControl<Button>("DetectFacesButton");
        var startCameraButton = this.FindControl<Button>("StartCameraButton");
        var clearButton = this.FindControl<Button>("ClearButton");
        var addPersonButton = this.FindControl<Button>("AddPersonButton");
        var advancedCameraButton = this.FindControl<Button>("StartAdvancedCameraButton");
        var clearAllButton = this.FindControl<Button>("ClearAllButton");

        if (loadButton != null)
            loadButton.Click += LoadImageButton_Click;
        
        if (detectButton != null)
            detectButton.Click += DetectFacesButton_Click;
        
        if (startCameraButton != null)
            startCameraButton.Click += StartCameraButton_Click;
        
        if (clearButton != null)
            clearButton.Click += ClearButton_Click;
        
        if (addPersonButton != null)
            addPersonButton.Click += AddPersonButton_Click;
        
        if (advancedCameraButton != null)
            advancedCameraButton.Click += StartAdvancedCameraButton_Click;
        
        if (clearAllButton != null)
            clearAllButton.Click += ClearAllButton_Click;
        
        // Kayıtlı kişileri yükle
        LoadKnownPeople();
    }

    private string GetPersonName()
    {
        var nameBox = this.FindControl<TextBox>("NewPersonNameBox");
        return nameBox?.Text ?? "Berkay";
    }

    private async void LoadKnownPeople()
    {
        try
        {
            var result = await RunPythonCommand("list_people");
            if (result != null && result.Success)
            {
                knownPeople = result.People ?? new List<string>();
                UpdatePeopleList();
            }
        }
        catch
        {
            // İlk çalıştırmada dosya olmayabilir
        }
    }

    private void UpdatePeopleList()
    {
        var panel = this.FindControl<StackPanel>("PeopleListPanel");
        var countText = this.FindControl<TextBlock>("PersonCountText");
        
        if (panel == null) return;
        
        panel.Children.Clear();
        
        if (countText != null)
            countText.Text = $"{knownPeople.Count} kişi kayıtlı";
        
        foreach (var person in knownPeople)
        {
            var personCard = new Border
            {
                Background = new Avalonia.Media.SolidColorBrush(Avalonia.Media.Color.Parse("#FF2D2D30")),
                CornerRadius = new Avalonia.CornerRadius(6),
                Padding = new Avalonia.Thickness(10, 8),
                BorderBrush = new Avalonia.Media.SolidColorBrush(Avalonia.Media.Color.Parse("#FF00E676")),
                BorderThickness = new Avalonia.Thickness(1)
            };
            
            var stackPanel = new StackPanel
            {
                Orientation = Avalonia.Layout.Orientation.Horizontal,
                Spacing = 10
            };
            
            var nameText = new TextBlock
            {
                Text = $"✅ {person}",
                FontSize = 14,
                Foreground = Avalonia.Media.Brushes.White,
                VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center
            };
            
            stackPanel.Children.Add(nameText);
            personCard.Child = stackPanel;
            panel.Children.Add(personCard);
        }
    }

    private async void AddPersonButton_Click(object? sender, RoutedEventArgs e)
    {
        var personName = GetPersonName();
        
        if (string.IsNullOrWhiteSpace(personName))
        {
            await ShowMessage("⚠️ Lütfen bir isim girin!");
            return;
        }
        
        var topLevel = TopLevel.GetTopLevel(this);
        if (topLevel == null) return;

        var files = await topLevel.StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = $"{personName} için fotoğraf seçin",
            AllowMultiple = false,
            FileTypeFilter = new[]
            {
                new FilePickerFileType("Görsel Dosyaları")
                {
                    Patterns = new[] { "*.jpg", "*.jpeg", "*.png", "*.bmp" }
                }
            }
        });

        if (files.Count > 0)
        {
            try
            {
                var file = files[0];
                var imagePath = file.Path.LocalPath;
                
                var result = await AddPersonToDatabase(imagePath, personName);
                
                if (result.Success)
                {
                    await ShowMessage($"✅ {personName} başarıyla eklendi!\n\nToplam {result.TotalPeople} kişi kayıtlı.\n\nŞimdi 'Gelişmiş Kamera'yı başlatabilirsiniz!");
                    LoadKnownPeople();
                    
                    // İsim kutusunu temizle
                    var nameBox = this.FindControl<TextBox>("NewPersonNameBox");
                    if (nameBox != null)
                        nameBox.Text = "";
                }
                else
                {
                    await ShowMessage($"❌ Hata: {result.Error}");
                }
            }
            catch (Exception ex)
            {
                await ShowMessage($"❌ Hata: {ex.Message}");
            }
        }
    }

    private async void StartAdvancedCameraButton_Click(object? sender, RoutedEventArgs e)
    {
        if (knownPeople.Count == 0)
        {
            await ShowMessage("⚠️ Henüz kayıtlı kişi yok!\n\nÖnce sol panelden kişi ekleyin.");
            return;
        }
        
        await ShowMessage($"🎥 Gelişmiş AI Kamera başlatılıyor...\n\n" +
                        $"✅ {knownPeople.Count} kişi tanınabilir: {string.Join(", ", knownPeople)}\n\n" +
                        $"• ESC: Çıkış\n" +
                        $"• SPACE: Ekran görüntüsü");
        
        try
        {
            await RunAdvancedCameraRecognition();
        }
        catch (Exception ex)
        {
            await ShowMessage($"❌ Kamera hatası: {ex.Message}");
        }
    }

    private async void ClearAllButton_Click(object? sender, RoutedEventArgs e)
    {
        var confirm = await ShowConfirmDialog("⚠️ Tüm kayıtlı kişileri silmek istediğinize emin misiniz?");
        
        if (confirm)
        {
            try
            {
                var dbPath = "face_database.pkl";
                if (File.Exists(dbPath))
                {
                    File.Delete(dbPath);
                    await ShowMessage("✅ Tüm kayıtlar silindi!");
                    LoadKnownPeople();
                }
            }
            catch (Exception ex)
            {
                await ShowMessage($"❌ Hata: {ex.Message}");
            }
        }
    }

    private async Task<PersonAddResult> AddPersonToDatabase(string imagePath, string personName)
    {
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "python3",
                Arguments = $"\"{advancedScript}\" add_person \"{cascadePath}\" \"{imagePath}\" \"{personName}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = Directory.GetCurrentDirectory()
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            
            await process.WaitForExitAsync();

            if (!string.IsNullOrWhiteSpace(error))
            {
                return new PersonAddResult { Success = false, Error = error };
            }

            var result = JsonSerializer.Deserialize<PersonAddResult>(output);
            return result ?? new PersonAddResult { Success = false, Error = "Geçersiz yanıt" };
        }
        catch (Exception ex)
        {
            return new PersonAddResult { Success = false, Error = ex.Message };
        }
    }

    private async Task<PeopleListResult?> RunPythonCommand(string command)
    {
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "python3",
                Arguments = $"\"{advancedScript}\" {command} \"{cascadePath}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = Directory.GetCurrentDirectory()
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            var output = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync();

            return JsonSerializer.Deserialize<PeopleListResult>(output);
        }
        catch
        {
            return null;
        }
    }

    private async Task RunAdvancedCameraRecognition()
    {
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "python3",
                Arguments = $"\"{advancedScript}\" recognize \"{cascadePath}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = false,
                WorkingDirectory = Directory.GetCurrentDirectory()
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            await process.WaitForExitAsync();
            
            await ShowMessage("✅ Kamera kapatıldı!");
        }
        catch (Exception ex)
        {
            await ShowMessage($"❌ Hata: {ex.Message}");
        }
    }

    private async Task<bool> ShowConfirmDialog(string message)
    {
        var result = false;
        var dialog = new Window
        {
            Title = "Onay",
            Width = 400,
            Height = 200,
            Content = new StackPanel
            {
                Margin = new Avalonia.Thickness(20),
                Spacing = 20,
                Children =
                {
                    new TextBlock 
                    { 
                        Text = message, 
                        TextWrapping = Avalonia.Media.TextWrapping.Wrap,
                        FontSize = 14
                    },
                    new StackPanel
                    {
                        Orientation = Avalonia.Layout.Orientation.Horizontal,
                        HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center,
                        Spacing = 10,
                        Children =
                        {
                            new Button 
                            { 
                                Content = "✅ Evet", 
                                Width = 100,
                                Height = 35,
                                Background = new Avalonia.Media.SolidColorBrush(Avalonia.Media.Color.Parse("#FFDC3545")),
                                Foreground = Avalonia.Media.Brushes.White
                            },
                            new Button 
                            { 
                                Content = "❌ Hayır", 
                                Width = 100,
                                Height = 35
                            }
                        }
                    }
                }
            }
        };

        var yesButton = ((dialog.Content as StackPanel)?.Children[1] as StackPanel)?.Children[0] as Button;
        var noButton = ((dialog.Content as StackPanel)?.Children[1] as StackPanel)?.Children[1] as Button;

        if (yesButton != null)
            yesButton.Click += (s, e) => { result = true; dialog.Close(); };
        
        if (noButton != null)
            noButton.Click += (s, e) => { result = false; dialog.Close(); };

        await dialog.ShowDialog(this);
        return result;
    }

    private async void LoadImageButton_Click(object? sender, RoutedEventArgs e)
    {
        var topLevel = TopLevel.GetTopLevel(this);
        if (topLevel == null) return;

        var files = await topLevel.StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = "Görsel Seç",
            AllowMultiple = false,
            FileTypeFilter = new[]
            {
                new FilePickerFileType("Görsel Dosyaları")
                {
                    Patterns = new[] { "*.jpg", "*.jpeg", "*.png", "*.bmp" }
                }
            }
        });

        if (files.Count > 0)
        {
            try
            {
                var file = files[0];
                currentImagePath = file.Path.LocalPath;
                
                // Görseli doğrudan Avalonia ile yükle
                using var stream = File.OpenRead(currentImagePath);
                var bitmap = new Bitmap(stream);
                
                var imageControl = this.FindControl<Image>("ImageDisplay");
                if (imageControl != null)
                {
                    imageControl.Source = bitmap;
                }
                
                // Placeholder'ı gizle
                var placeholder = this.FindControl<StackPanel>("PlaceholderPanel");
                if (placeholder != null)
                    placeholder.IsVisible = false;
                
                await ShowMessage($"✓ Görsel başarıyla yüklendi!\n\nŞimdi 'Yüzleri Tespit Et' butonuna basabilir\nveya kamerayı başlatarak {GetPersonName()} olarak tanınabilirsiniz!");
            }
            catch (Exception ex)
            {
                await ShowMessage($"Görsel yüklenirken hata: {ex.Message}");
            }
        }
    }

    private async void StartCameraButton_Click(object? sender, RoutedEventArgs e)
    {
        try
        {
            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "python3",
                    Arguments = "camera_detector.py",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = false
                }
            };

            process.Start();
            await ShowMessage("🎥 Kamera başlatıldı!\n\nESC tuşu ile kapatabilirsiniz.");
        }
        catch (Exception ex)
        {
            await ShowMessage($"Hata: {ex.Message}");
        }
    }

    private async void DetectFacesButton_Click(object? sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(currentImagePath))
        {
            await ShowMessage("Lütfen önce bir görsel yükleyin!");
            return;
        }
        
        if (!File.Exists(cascadePath))
        {
            await ShowMessage($"Haar Cascade dosyası bulunamadı!\n\n" +
                            $"'{cascadePath}' dosyasını proje klasörüne eklemeniz gerekiyor.");
            return;
        }

        if (!File.Exists(pythonScript))
        {
            await ShowMessage($"Python script dosyası bulunamadı!\n\n" +
                            $"'{pythonScript}' dosyası eksik.");
            return;
        }

        try
        {
            // Python script'ini çalıştır
            var result = await RunPythonFaceDetection(currentImagePath, cascadePath);
            
            if (result.Success)
            {
                // İşlenmiş görseli göster
                if (!string.IsNullOrEmpty(result.OutputPath) && File.Exists(result.OutputPath))
                {
                    using var stream = File.OpenRead(result.OutputPath);
                    var bitmap = new Bitmap(stream);
                    
                    var imageControl = this.FindControl<Image>("ImageDisplay");
                    if (imageControl != null)
                    {
                        imageControl.Source = bitmap;
                    }
                }
                
                await ShowMessage($"✓ {result.FaceCount} yüz tespit edildi!");
            }
            else
            {
                await ShowMessage($"Hata: {result.Error}");
            }
        }
        catch (Exception ex)
        {
            await ShowMessage($"Hata: {ex.Message}");
        }
    }

    private async Task<FaceDetectionResult> RunPythonFaceDetection(string imagePath, string cascadePath)
    {
        try
        {
            var personName = GetPersonName();
            var startInfo = new ProcessStartInfo
            {
                FileName = "python3",
                Arguments = $"\"{pythonScript}\" \"{imagePath}\" \"{cascadePath}\" \"{personName}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = Directory.GetCurrentDirectory()
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            
            await process.WaitForExitAsync();

            if (!string.IsNullOrWhiteSpace(error))
            {
                return new FaceDetectionResult { Success = false, Error = error };
            }

            // JSON çıktısını parse et
            var result = JsonSerializer.Deserialize<FaceDetectionResult>(output);
            return result ?? new FaceDetectionResult { Success = false, Error = "Geçersiz yanıt" };
        }
        catch (Exception ex)
        {
            return new FaceDetectionResult { Success = false, Error = ex.Message };
        }
    }    private void ClearButton_Click(object? sender, RoutedEventArgs e)
    {
        currentImagePath = null;
        
        var imageDisplay = this.FindControl<Avalonia.Controls.Image>("ImageDisplay");
        if (imageDisplay != null)
            imageDisplay.Source = null;
        
        // Placeholder'ı göster
        var placeholder = this.FindControl<StackPanel>("PlaceholderPanel");
        if (placeholder != null)
            placeholder.IsVisible = true;
    }

    private async Task RunCameraFaceDetection(string cascadePath, string? referenceImage)
    {
        try
        {
            var personName = GetPersonName();
            var args = $"\"{cameraScript}\" \"{cascadePath}\"";
            if (!string.IsNullOrEmpty(referenceImage))
            {
                args += $" \"{referenceImage}\" \"{personName}\"";
            }

            var startInfo = new ProcessStartInfo
            {
                FileName = "python3",
                Arguments = args,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = false, // Kamera penceresi için false
                WorkingDirectory = Directory.GetCurrentDirectory()
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            // Asenkron olarak çıktıları oku
            var outputTask = process.StandardOutput.ReadToEndAsync();
            var errorTask = process.StandardError.ReadToEndAsync();
            
            await process.WaitForExitAsync();

            var output = await outputTask;
            var error = await errorTask;

            if (!string.IsNullOrWhiteSpace(error))
            {
                await ShowMessage($"Kamera hatası: {error}");
                return;
            }

            // JSON sonucu parse et ve göster
            try
            {
                var result = JsonSerializer.Deserialize<CameraDetectionResult>(output);
                if (result != null && result.Success)
                {
                    await ShowMessage($"✓ Kamera kapatıldı!\n\n" +
                                    $"Toplam tespit edilen yüz: {result.TotalFacesDetected}\n" +
                                    $"İşlenen kare sayısı: {result.FramesProcessed}\n" +
                                    $"Ortalama yüz/kare: {result.AverageFacesPerFrame}");
                }
            }
            catch
            {
                // JSON parse edilemezse sessizce devam et
            }
        }
        catch (Exception ex)
        {
            await ShowMessage($"Kamera başlatma hatası: {ex.Message}");
        }
    }

    private async Task ShowMessage(string message)
    {
        var messageBox = new Avalonia.Controls.Window
        {
            Title = "Bilgi",
            Width = 400,
            Height = 200,
            Content = new StackPanel
            {
                Margin = new Avalonia.Thickness(20),
                Spacing = 15,
                Children =
                {
                    new TextBlock 
                    { 
                        Text = message, 
                        TextWrapping = Avalonia.Media.TextWrapping.Wrap,
                        FontSize = 14
                    },
                    new Button 
                    { 
                        Content = "Tamam", 
                        HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center,
                        Width = 100,
                        Height = 35
                    }
                }
            }
        };

        var button = (messageBox.Content as StackPanel)?.Children.OfType<Button>().First();
        if (button != null)
            button.Click += (s, e) => messageBox.Close();

        await messageBox.ShowDialog(this);
    }
}

// Python'dan gelen JSON yanıtı için model
public class FaceDetectionResult
{
    [System.Text.Json.Serialization.JsonPropertyName("success")]
    public bool Success { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("face_count")]
    public int FaceCount { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("output_path")]
    public string? OutputPath { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("error")]
    public string? Error { get; set; }
}

// Kamera tespiti için model
public class CameraDetectionResult
{
    [System.Text.Json.Serialization.JsonPropertyName("success")]
    public bool Success { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("total_faces_detected")]
    public int TotalFacesDetected { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("frames_processed")]
    public int FramesProcessed { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("average_faces_per_frame")]
    public double AverageFacesPerFrame { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("error")]
    public string? Error { get; set; }
}

// Kişi ekleme sonucu
public class PersonAddResult
{
    [System.Text.Json.Serialization.JsonPropertyName("success")]
    public bool Success { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("message")]
    public string? Message { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("total_people")]
    public int TotalPeople { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("error")]
    public string? Error { get; set; }
}

// Kişi listesi sonucu
public class PeopleListResult
{
    [System.Text.Json.Serialization.JsonPropertyName("success")]
    public bool Success { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("people")]
    public List<string>? People { get; set; }
    
    [System.Text.Json.Serialization.JsonPropertyName("count")]
    public int Count { get; set; }
}
