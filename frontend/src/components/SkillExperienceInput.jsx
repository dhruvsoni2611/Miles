import React from 'react';

const SkillExperienceInput = ({
  selectedSkills = [],
  experienceData = {},
  onExperienceChange,
  placeholder = "Enter experience..."
}) => {
  const handleExperienceChange = (skill, years, months) => {
    // Convert years and months to total months
    const totalMonths = (parseInt(years) || 0) * 12 + (parseInt(months) || 0);

    const newExperienceData = {
      ...experienceData,
      [skill]: totalMonths
    };

    // Remove experience entry if both fields are empty
    if (totalMonths === 0) {
      delete newExperienceData[skill];
    }

    onExperienceChange(newExperienceData);
  };

  const getExperienceForSkill = (skill) => {
    const totalMonths = experienceData[skill] || 0;
    return {
      years: Math.floor(totalMonths / 12),
      months: totalMonths % 12
    };
  };

  if (selectedSkills.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic">
        {placeholder}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">
        Experience for Selected Skills (in months)
      </label>

      {selectedSkills.map((skill, index) => {
        const experience = getExperienceForSkill(skill);

        return (
          <div key={index} className="bg-gray-50 p-3 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-gray-900">{skill}</span>
              <span className="text-xs text-gray-500">
                Total: {experience.years * 12 + experience.months} months
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">
                  Years
                </label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={experience.years}
                  onChange={(e) => handleExperienceChange(skill, e.target.value, experience.months)}
                  className="w-full px-2 py-1 text-sm bg-white border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-black"
                  placeholder="0"
                />
              </div>

              <div>
                <label className="block text-xs text-gray-600 mb-1">
                  Months
                </label>
                <input
                  type="number"
                  min="0"
                  max="11"
                  value={experience.months}
                  onChange={(e) => handleExperienceChange(skill, experience.years, e.target.value)}
                  className="w-full px-2 py-1 text-sm bg-white border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-black"
                  placeholder="0"
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SkillExperienceInput;