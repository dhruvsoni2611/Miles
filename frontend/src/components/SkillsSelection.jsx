import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const SkillsSelection = ({ selectedSkills = [], onSkillsChange, placeholder = "Select skills..." }) => {
  const { ensureValidSession } = useAuth();
  const [categories, setCategories] = useState([]);
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  // Load categories on component mount
  useEffect(() => {
    loadCategories();
  }, []);

  // Load skills when category changes
  useEffect(() => {
    if (selectedCategory) {
      loadSkills(selectedCategory);
    } else {
      setSkills([]);
    }
  }, [selectedCategory]);

  const loadCategories = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = await ensureValidSession();

      const response = await fetch('http://localhost:8000/api/skills/categories', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load categories: ${response.status}`);
      }

      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Error loading categories:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSkills = async (category) => {
    try {
      setLoading(true);
      setError(null);

      const token = await ensureValidSession();

      const response = await fetch(`http://localhost:8000/api/skills?category=${encodeURIComponent(category)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load skills: ${response.status}`);
      }

      const data = await response.json();
      setSkills(data.skills || []);
    } catch (error) {
      console.error('Error loading skills:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSkillSelect = (skill) => {
    const skillName = skill.name;
    if (!selectedSkills.includes(skillName)) {
      const newSkills = [...selectedSkills, skillName];
      onSkillsChange(newSkills);
    }
  };

  const handleSkillRemove = (skillToRemove) => {
    const newSkills = selectedSkills.filter(skill => skill !== skillToRemove);
    onSkillsChange(newSkills);
  };

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
    setShowDropdown(true);
  };

  return (
    <div className="space-y-3">
      {/* Category Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Skill Category
        </label>
        <select
          value={selectedCategory}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className="w-full px-3 py-2 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
        >
          <option value="">Select a category</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        {loading && <p className="text-sm text-gray-500 mt-1">Loading...</p>}
        {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
      </div>

      {/* Skills Selection */}
      {selectedCategory && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Available Skills in {selectedCategory}
          </label>
          <div className="relative">
            <select
              value=""
              onChange={(e) => {
                const skillId = e.target.value;
                const skill = skills.find(s => s.id === skillId);
                if (skill) handleSkillSelect(skill);
                e.target.value = ''; // Reset select
              }}
              className="w-full px-3 py-2 bg-white border border-black rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black transition-colors"
            >
              <option value="">Select skills from {selectedCategory}</option>
              {skills
                .filter(skill => !selectedSkills.includes(skill.name))
                .map((skill) => (
                  <option key={skill.id} value={skill.id}>
                    {skill.name}
                  </option>
                ))}
            </select>
          </div>
        </div>
      )}

      {/* Selected Skills Display */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Selected Skills
        </label>
        <div className="min-h-[80px] p-3 bg-gray-50 border border-gray-200 rounded-lg">
          {selectedSkills.length === 0 ? (
            <p className="text-gray-400 text-sm italic">{placeholder}</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {selectedSkills.map((skill, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800 border border-blue-200"
                >
                  {skill}
                  <button
                    onClick={() => handleSkillRemove(skill)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SkillsSelection;
