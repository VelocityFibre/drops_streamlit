-- QA Photo Reviews Schema for Neon Database
-- This schema tracks photo completion for fiber installation QA reviews

-- Main QA Photo Reviews table - tracks photo completion status for each drop
CREATE TABLE qa_photo_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drop_number VARCHAR(50) NOT NULL,
  review_date DATE NOT NULL DEFAULT CURRENT_DATE,
  user_name VARCHAR(100) NOT NULL,
  
  -- Step completion fields (14 required photo steps)
  step_01_property_frontage BOOLEAN DEFAULT FALSE,
  step_02_location_before_install BOOLEAN DEFAULT FALSE,
  step_03_outside_cable_span BOOLEAN DEFAULT FALSE,
  step_04_home_entry_outside BOOLEAN DEFAULT FALSE,
  step_05_home_entry_inside BOOLEAN DEFAULT FALSE,
  step_06_fibre_entry_to_ont BOOLEAN DEFAULT FALSE,
  step_07_patched_labelled_drop BOOLEAN DEFAULT FALSE,
  step_08_work_area_completion BOOLEAN DEFAULT FALSE,
  step_09_ont_barcode_scan BOOLEAN DEFAULT FALSE,
  step_10_ups_serial_number BOOLEAN DEFAULT FALSE,
  step_11_powermeter_reading BOOLEAN DEFAULT FALSE,
  step_12_powermeter_at_ont BOOLEAN DEFAULT FALSE,
  step_13_active_broadband_light BOOLEAN DEFAULT FALSE,
  step_14_customer_signature BOOLEAN DEFAULT FALSE,
  
  -- Auto-calculated summary fields
  completed_photos INTEGER GENERATED ALWAYS AS (
    (CASE WHEN step_01_property_frontage THEN 1 ELSE 0 END) +
    (CASE WHEN step_02_location_before_install THEN 1 ELSE 0 END) +
    (CASE WHEN step_03_outside_cable_span THEN 1 ELSE 0 END) +
    (CASE WHEN step_04_home_entry_outside THEN 1 ELSE 0 END) +
    (CASE WHEN step_05_home_entry_inside THEN 1 ELSE 0 END) +
    (CASE WHEN step_06_fibre_entry_to_ont THEN 1 ELSE 0 END) +
    (CASE WHEN step_07_patched_labelled_drop THEN 1 ELSE 0 END) +
    (CASE WHEN step_08_work_area_completion THEN 1 ELSE 0 END) +
    (CASE WHEN step_09_ont_barcode_scan THEN 1 ELSE 0 END) +
    (CASE WHEN step_10_ups_serial_number THEN 1 ELSE 0 END) +
    (CASE WHEN step_11_powermeter_reading THEN 1 ELSE 0 END) +
    (CASE WHEN step_12_powermeter_at_ont THEN 1 ELSE 0 END) +
    (CASE WHEN step_13_active_broadband_light THEN 1 ELSE 0 END) +
    (CASE WHEN step_14_customer_signature THEN 1 ELSE 0 END)
  ) STORED,
  
  outstanding_photos INTEGER GENERATED ALWAYS AS (
    14 - (
      (CASE WHEN step_01_property_frontage THEN 1 ELSE 0 END) +
      (CASE WHEN step_02_location_before_install THEN 1 ELSE 0 END) +
      (CASE WHEN step_03_outside_cable_span THEN 1 ELSE 0 END) +
      (CASE WHEN step_04_home_entry_outside THEN 1 ELSE 0 END) +
      (CASE WHEN step_05_home_entry_inside THEN 1 ELSE 0 END) +
      (CASE WHEN step_06_fibre_entry_to_ont THEN 1 ELSE 0 END) +
      (CASE WHEN step_07_patched_labelled_drop THEN 1 ELSE 0 END) +
      (CASE WHEN step_08_work_area_completion THEN 1 ELSE 0 END) +
      (CASE WHEN step_09_ont_barcode_scan THEN 1 ELSE 0 END) +
      (CASE WHEN step_10_ups_serial_number THEN 1 ELSE 0 END) +
      (CASE WHEN step_11_powermeter_reading THEN 1 ELSE 0 END) +
      (CASE WHEN step_12_powermeter_at_ont THEN 1 ELSE 0 END) +
      (CASE WHEN step_13_active_broadband_light THEN 1 ELSE 0 END) +
      (CASE WHEN step_14_customer_signature THEN 1 ELSE 0 END)
    )
  ) STORED,
  
  -- Additional fields
  outstanding_photos_loaded_to_1map BOOLEAN DEFAULT FALSE,
  comment TEXT,
  
  -- Audit fields
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Ensure unique entry per drop number and date
  UNIQUE(drop_number, review_date)
);

-- QA Review Steps lookup table - defines the 14 photo steps
CREATE TABLE qa_review_steps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  step_number INTEGER NOT NULL UNIQUE,
  step_title VARCHAR(200) NOT NULL,
  step_description TEXT NOT NULL
);

-- Insert the 14 QA review steps with detailed descriptions
INSERT INTO qa_review_steps (step_number, step_title, step_description) VALUES
(1, 'Property Frontage – house, street number visible', 'Wide shot of house, street number visible'),
(2, 'Location on Wall (Before Install)', 'Show intended ONT spot + power outlet'),
(3, 'Outside Cable Span (Pole → Pigtail screw)', 'Wide shot showing full span (Pole → Pigtail screw)'),
(4, 'Home Entry Point – Outside', 'Close-up of pigtail screw/duct entry'),
(5, 'Home Entry Point – Inside', 'Inside view of same entry penetration'),
(6, 'Fibre Entry to ONT (After Install)', 'Show slack loop + clips/conduit'),
(7, 'Patched & Labelled Drop', 'Label with Drop Number visible'),
(8, 'Overall Work Area After Completion', 'ONT, fibre routing & electrical outlet in frame'),
(9, 'ONT Barcode – Scan barcode + photo of label', 'Scan barcode + photo of label'),
(10, 'Mini-UPS Serial Number (Gizzu)', 'Scan/enter serial + photo of label'),
(11, 'Powermeter Reading (Drop/Feeder)', 'Enter dBm + photo of meter screen'),
(12, 'Powermeter at ONT (Before Activation)', 'Enter dBm + photo of meter screen. Acceptable: −25 to −10 dBm'),
(13, 'Active Broadband Light', 'ONT light ON + Fibertime sticker + Drop No.'),
(14, 'Customer Signature', 'Collect digital signature + customer name in 1Map');

-- Performance indexes
CREATE INDEX idx_qa_photo_reviews_date ON qa_photo_reviews(review_date);
CREATE INDEX idx_qa_photo_reviews_user ON qa_photo_reviews(user_name);
CREATE INDEX idx_qa_photo_reviews_drop_number ON qa_photo_reviews(drop_number);
CREATE INDEX idx_qa_photo_reviews_outstanding ON qa_photo_reviews(outstanding_photos) WHERE outstanding_photos > 0;

-- Comments explaining the schema
COMMENT ON TABLE qa_photo_reviews IS 'Tracks QA photo completion status for fiber installation drops';
COMMENT ON COLUMN qa_photo_reviews.drop_number IS 'Unique identifier for the fiber drop installation';
COMMENT ON COLUMN qa_photo_reviews.completed_photos IS 'Auto-calculated count of completed photo steps (0-14)';
COMMENT ON COLUMN qa_photo_reviews.outstanding_photos IS 'Auto-calculated count of missing photo steps (14 - completed)';
COMMENT ON COLUMN qa_photo_reviews.outstanding_photos_loaded_to_1map IS 'Flag indicating if outstanding photos have been loaded to 1Map system';

-- Sample data queries for reference:
/*
-- Get all reviews with outstanding photos
SELECT drop_number, user_name, review_date, completed_photos, outstanding_photos, comment
FROM qa_photo_reviews 
WHERE outstanding_photos > 0 
ORDER BY outstanding_photos DESC, review_date DESC;

-- Get completion summary by user
SELECT 
  user_name,
  COUNT(*) as total_reviews,
  ROUND(AVG(completed_photos), 2) as avg_completed_photos,
  ROUND(AVG(outstanding_photos), 2) as avg_outstanding_photos,
  COUNT(CASE WHEN outstanding_photos = 0 THEN 1 END) as fully_complete_reviews
FROM qa_photo_reviews 
GROUP BY user_name 
ORDER BY avg_completed_photos DESC;

-- Get daily completion trends
SELECT 
  review_date,
  COUNT(*) as reviews_count,
  ROUND(AVG(completed_photos), 2) as avg_completed,
  COUNT(CASE WHEN outstanding_photos = 0 THEN 1 END) as fully_complete
FROM qa_photo_reviews 
GROUP BY review_date 
ORDER BY review_date DESC;
*/